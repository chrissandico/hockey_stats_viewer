/**
 * Hockey Stats Web Application - Mobile Optimizations
 * 
 * This file contains JavaScript functions for optimizing the application
 * on mobile devices, including collapsible sections, touch event handling,
 * and responsive table adjustments.
 */

// Wait for the document to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize mobile optimizations
    initMobileOptimizations();
});

/**
 * Initialize mobile optimizations
 */
function initMobileOptimizations() {
    // Set up collapsible sections
    setupCollapsibleSections();
    
    // Add touch-friendly event listeners
    setupTouchEvents();
    
    // Make tables responsive
    makeTablesResponsive();
    
    // Add orientation change handler
    window.addEventListener('orientationchange', handleOrientationChange);
}

/**
 * Set up collapsible sections for mobile devices
 */
function setupCollapsibleSections() {
    // Find all collapsible headers
    const collapsibleHeaders = document.querySelectorAll('.collapsible-header');
    
    // Add click event listeners to each header
    collapsibleHeaders.forEach(header => {
        header.addEventListener('click', function() {
            // Toggle the 'active' class on the header
            this.classList.toggle('active');
            
            // Get the content element
            const content = this.nextElementSibling;
            
            // Toggle the visibility of the content
            if (content.style.maxHeight) {
                content.style.maxHeight = null;
            } else {
                content.style.maxHeight = content.scrollHeight + 'px';
            }
        });
    });
}

/**
 * Set up touch-friendly event listeners
 */
function setupTouchEvents() {
    // Add touch event listeners to buttons and links
    const touchElements = document.querySelectorAll('.btn, .nav-link, .dropdown-item');
    
    touchElements.forEach(element => {
        // Add active state on touch start
        element.addEventListener('touchstart', function() {
            this.classList.add('touch-active');
        });
        
        // Remove active state on touch end
        element.addEventListener('touchend', function() {
            this.classList.remove('touch-active');
        });
        
        // Remove active state if touch is moved away
        element.addEventListener('touchmove', function() {
            this.classList.remove('touch-active');
        });
    });
}

/**
 * Make tables responsive on mobile devices
 */
function makeTablesResponsive() {
    // Find all tables
    const tables = document.querySelectorAll('table');
    
    // Add responsive class to tables that aren't already wrapped
    tables.forEach(table => {
        // Check if the table is already in a responsive wrapper
        if (!table.parentElement.classList.contains('table-responsive')) {
            // Create a responsive wrapper
            const wrapper = document.createElement('div');
            wrapper.classList.add('table-responsive');
            
            // Replace the table with the wrapper containing the table
            table.parentNode.insertBefore(wrapper, table);
            wrapper.appendChild(table);
        }
    });
}

/**
 * Handle orientation change events
 */
function handleOrientationChange() {
    // Adjust layout when device orientation changes
    setTimeout(function() {
        // Reset any fixed heights on collapsible content
        const activeCollapsibles = document.querySelectorAll('.collapsible-header.active + .collapsible-content');
        activeCollapsibles.forEach(content => {
            content.style.maxHeight = content.scrollHeight + 'px';
        });
        
        // Refresh table responsive wrappers
        makeTablesResponsive();
    }, 200);
}

/**
 * Create a collapsible section dynamically
 * 
 * @param {string} title - The title of the collapsible section
 * @param {HTMLElement} content - The content element to make collapsible
 * @param {boolean} startCollapsed - Whether the section should start collapsed
 * @return {HTMLElement} The created collapsible section
 */
function createCollapsibleSection(title, content, startCollapsed = true) {
    // Create the section container
    const section = document.createElement('div');
    section.classList.add('collapsible-section');
    
    // Create the header
    const header = document.createElement('div');
    header.classList.add('collapsible-header');
    if (!startCollapsed) {
        header.classList.add('active');
    }
    header.textContent = title;
    
    // Create the content wrapper
    const contentWrapper = document.createElement('div');
    contentWrapper.classList.add('collapsible-content');
    if (!startCollapsed) {
        contentWrapper.style.maxHeight = content.scrollHeight + 'px';
    }
    
    // Add the content to the wrapper
    contentWrapper.appendChild(content);
    
    // Add the header and content wrapper to the section
    section.appendChild(header);
    section.appendChild(contentWrapper);
    
    // Add click event listener to the header
    header.addEventListener('click', function() {
        this.classList.toggle('active');
        
        if (contentWrapper.style.maxHeight) {
            contentWrapper.style.maxHeight = null;
        } else {
            contentWrapper.style.maxHeight = contentWrapper.scrollHeight + 'px';
        }
    });
    
    return section;
}

/**
 * Check if the device is mobile
 * 
 * @return {boolean} True if the device is mobile, false otherwise
 */
function isMobileDevice() {
    return window.innerWidth <= 768;
}

/**
 * Apply mobile optimizations to a specific element
 * 
 * @param {HTMLElement} element - The element to optimize for mobile
 */
function optimizeElementForMobile(element) {
    if (isMobileDevice()) {
        // Add mobile-specific classes
        element.classList.add('mobile-optimized');
        
        // Find tables within the element and make them responsive
        const tables = element.querySelectorAll('table');
        tables.forEach(table => {
            if (!table.parentElement.classList.contains('table-responsive')) {
                const wrapper = document.createElement('div');
                wrapper.classList.add('table-responsive');
                table.parentNode.insertBefore(wrapper, table);
                wrapper.appendChild(table);
            }
        });
    }
}
