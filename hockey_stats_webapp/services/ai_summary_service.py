import os
import json
import logging
import hashlib
import config
from dotenv import load_dotenv, find_dotenv

logger = logging.getLogger(__name__)

class AISummaryService:
    """
    Service for generating AI Game Analyst Summaries using Anthropic Claude models.
    Supports Coach mode (tactical video analyst) and Parent mode (positive beat reporter).
    Includes in-memory/disk caching and deterministic fallback recap generation.
    """

    def __init__(self, cache_dir=None):
        load_dotenv(find_dotenv())
        self.api_key = os.environ.get('ANTHROPIC_API_KEY')
        self.model = getattr(config, 'ANTHROPIC_MODEL', 'claude-3-5-sonnet-20241022')
        self._cache = {}

        # Setup persistent cache path
        if cache_dir is None:
            cache_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
        os.makedirs(cache_dir, exist_ok=True)
        self.cache_file = os.path.join(cache_dir, 'summaries_cache.json')
        self._load_disk_cache()

        # Initialize Anthropic client if available
        self.client = None
        if self.api_key:
            try:
                import anthropic
                self.client = anthropic.Anthropic(api_key=self.api_key)
                logger.info(f"AISummaryService initialized with Anthropic model '{self.model}'")
            except ImportError:
                logger.warning("anthropic package not installed. AISummaryService running in fallback mode.")
            except Exception as e:
                logger.error(f"Failed to initialize Anthropic client: {e}")
        else:
            logger.info("ANTHROPIC_API_KEY not found in environment. AISummaryService running in deterministic fallback mode.")

    def _load_disk_cache(self):
        """Load cached summaries from disk."""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    self._cache = json.load(f)
            except Exception as e:
                logger.warning(f"Error loading AI summary disk cache: {e}")
                self._cache = {}

    def _save_disk_cache(self):
        """Save cached summaries to disk."""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self._cache, f, indent=2)
        except Exception as e:
            logger.warning(f"Error saving AI summary disk cache: {e}")

    def clear_cache(self, game_id=None):
        """
        Clear cached summaries.
        If game_id is provided, clears entries for that game.
        Otherwise, clears all cached summaries.
        """
        if game_id is None:
            self._cache = {}
        else:
            str_id = str(game_id)
            keys_to_remove = [k for k in self._cache if k.startswith(f"{str_id}:")]
            for k in keys_to_remove:
                self._cache.pop(k, None)
        self._save_disk_cache()

    def generate_summary(self, game_digest: dict, mode: str = 'coach', force_refresh: bool = False) -> str:
        """
        Generate or retrieve a game analyst summary for the given game digest and mode.

        Args:
            game_digest (dict): Ultra-compact structured game summary payload
            mode (str): 'coach' or 'parent'
            force_refresh (bool): Force API call bypassing cache

        Returns:
            str: Generated summary text
        """
        if not game_digest or 'game' not in game_digest:
            return "No game data available for summary analysis."

        game_id = str(game_digest['game'].get('ID', 'unknown'))
        # Generate hash of digest content so any change in stats automatically invalidates cache
        digest_str = json.dumps(game_digest, sort_keys=True)
        digest_hash = hashlib.md5(digest_str.encode('utf-8')).hexdigest()[:8]
        cache_key = f"{game_id}:{mode}:{digest_hash}"

        # 1. Return from cache if available
        if not force_refresh and cache_key in self._cache:
            logger.debug(f"AI summary cache hit for key '{cache_key}'")
            return self._cache[cache_key]

        # 2. Call Anthropic API if client is configured
        if self.client:
            try:
                system_prompt = (
                    getattr(config, 'COACH_SYSTEM_PROMPT', '')
                    if mode == 'coach'
                    else getattr(config, 'PARENT_SYSTEM_PROMPT', '')
                )

                logger.info(f"Generating AI summary via Anthropic for game '{game_id}', mode='{mode}'")

                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=600,
                    system=system_prompt,
                    messages=[{
                        "role": "user",
                        "content": (
                            f"Analyze this game digest and generate a professional {mode} recap. "
                            f"Do not surround your text in markdown code blocks:\n\n"
                            f"{json.dumps(game_digest, indent=2)}"
                        )
                    }]
                )

                if response and response.content:
                    summary_text = response.content[0].text.strip()
                    self._cache[cache_key] = summary_text
                    self._save_disk_cache()
                    return summary_text

            except Exception as e:
                logger.error(f"Error generating AI summary via Anthropic API: {e}")

        # 3. Fallback to deterministic template summary
        logger.info(f"Using fallback summary builder for game '{game_id}', mode='{mode}'")
        summary_text = self._generate_fallback_summary(game_digest, mode)
        self._cache[cache_key] = summary_text
        self._save_disk_cache()
        return summary_text

    def _generate_fallback_summary(self, digest: dict, mode: str) -> str:
        """Generate a structured, data-grounded summary using actual game statistics."""
        game = digest.get('game', {})
        opp = game.get('Opponent', 'Opponent')
        gf = game.get('GoalsFor', 0)
        ga = game.get('GoalsAgainst', 0)
        sf = game.get('ShotsFor', digest.get('possession', {}).get('shots_for', 0))
        sa = game.get('ShotsAgainst', digest.get('possession', {}).get('shots_against', 0))
        res = str(game.get('Result', '')).upper()
        date_str = game.get('Date', '')

        result_phrase = "won" if "W" in res else ("lost" if "L" in res else "tied")
        st = digest.get('special_teams', {})
        possession = digest.get('possession', {})
        scorers = digest.get('top_scorers', [])
        scorers_str = ", ".join(scorers) if scorers else ""

        if mode == 'coach':
            if gf == 0:
                p1 = (
                    f"Game Recap ({date_str}): The team was shut out {gf}-{ga} against {opp}. "
                    f"Despite putting {sf} shots on goal (vs. {sa} shots allowed), the offense generated zero goals and struggled to create high-danger scoring chances."
                )
                p2 = (
                    f"Analytics & Possession: On special teams, the Power Play was {st.get('pp_pct', '0%')} "
                    f"({st.get('pp_goals', 0)}/{st.get('pp_opportunities', 0)}) with {st.get('pp_shots_per_opp', 0)} shots per PP opportunity. "
                    f"The Penalty Kill was {st.get('pk_pct', '100%')}. "
                    f"At 5v5, Corsi shot share was {possession.get('shot_share_pct', '50%')} ({sf} shots for vs {sa} shots against)."
                )
                p3 = (
                    f"Tactical Focus: Video breakdown must focus on net-front presence, generating high-danger scoring chances, "
                    f"and improving shot conversion, as {sf} perimeter shots produced no goals."
                )
            else:
                p1 = (
                    f"Game Recap ({date_str}): The team {result_phrase} against {opp} with a final score of {gf}-{ga} "
                    f"(outshooting opponent {sf}-{sa})."
                )
                p2 = (
                    f"Analytics & Possession: Power Play operated at {st.get('pp_pct', '0%')} "
                    f"({st.get('pp_goals', 0)}/{st.get('pp_opportunities', 0)}) with {st.get('pp_shots_per_opp', 0)} shots/PP. "
                    f"Penalty Kill held a {st.get('pk_pct', '100%')} efficiency. "
                    f"5v5 Corsi shot share reached {possession.get('shot_share_pct', '50%')} ({sf} SF vs {sa} SA)."
                )
                p3 = (
                    f"Tactical Focus & Scorers: Key contributors: {scorers_str or 'balanced team effort'}. "
                    f"Practice focus areas: gap control, zone exit support, and power play puck movement."
                )
            return f"{p1}\n\n{p2}\n\n{p3}"
        else:
            if gf == 0:
                p1 = (
                    f"Game Recap ({date_str}): Our team faced {opp} in a tough contest, finishing with a final score of {gf}-{ga}. "
                    f"While the team was held goalless, the players fought hard and generated {sf} shot attempts."
                )
                p2 = (
                    f"Game Highlights: Goaltending and defense faced {sa} shots against, showing strong communication and relentless hustle under pressure."
                )
                p3 = (
                    f"Looking Ahead: The team showed great determination and resilience despite the score. "
                    f"Let's build on the {sf}-shot effort and get ready for the next game!"
                )
            else:
                p1 = (
                    f"Game Recap ({date_str}): Our team took the ice against {opp} in an exciting contest, "
                    f"finishing with a final score of {gf}-{ga} ({sf} total shots)."
                )
                p2 = (
                    f"Game Highlights: Offense was led by {scorers_str or 'great teamwork'}. "
                    f"The team showed fantastic communication and energy on defense and in goal."
                )
                p3 = (
                    f"Looking Ahead: Great effort across all shifts! Let's keep building this momentum for the next game."
                )
            return f"{p1}\n\n{p2}\n\n{p3}"
