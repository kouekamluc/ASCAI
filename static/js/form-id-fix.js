/**
 * Fix duplicate form field IDs
 * Ensures all form fields have unique IDs to prevent autofill issues
 */
(function() {
    'use strict';
    
    function fixDuplicateIds() {
        // Find all form fields (input, select, textarea)
        const formFields = document.querySelectorAll('input, select, textarea');
        const idMap = new Map();
        const duplicateIds = new Set();
        
        // First pass: identify duplicates
        formFields.forEach(function(field) {
            const id = field.id;
            if (id) {
                if (idMap.has(id)) {
                    duplicateIds.add(id);
                    idMap.get(id).push(field);
                } else {
                    idMap.set(id, [field]);
                }
            }
        });
        
        // Second pass: fix duplicates
        duplicateIds.forEach(function(duplicateId) {
            const fields = idMap.get(duplicateId);
            
            // Find the form each field belongs to
            fields.forEach(function(field, index) {
                if (index === 0) {
                    // Keep the first one as is
                    return;
                }
                
                // Generate a unique ID based on form context
                let newId = duplicateId;
                const form = field.closest('form');
                
                if (form) {
                    // Try to use form id or name
                    const formId = form.id || form.name || form.getAttribute('name');
                    if (formId) {
                        newId = formId + '_' + duplicateId;
                    } else {
                        // Use form index as fallback
                        const forms = document.querySelectorAll('form');
                        const formIndex = Array.from(forms).indexOf(form);
                        newId = 'form_' + formIndex + '_' + duplicateId;
                    }
                    
                    // Ensure the new ID is also unique
                    let counter = 1;
                    while (document.getElementById(newId)) {
                        newId = duplicateId + '_' + counter;
                        counter++;
                    }
                } else {
                    // No form parent, use index
                    newId = duplicateId + '_' + index;
                }
                
                // Update the field ID
                field.id = newId;
                
                // Update associated labels
                const labels = document.querySelectorAll('label[for="' + duplicateId + '"]');
                labels.forEach(function(label) {
                    // Check if this label is associated with this specific field
                    const labelForm = label.closest('form');
                    const labelFormGroup = label.closest('.form-group');
                    const fieldFormGroup = field.closest('.form-group');
                    
                    // Update label if it's in the same form/form-group as this field
                    if ((labelForm === form || !labelForm) && 
                        (labelFormGroup === fieldFormGroup || !labelFormGroup || index === 1)) {
                        label.setAttribute('for', newId);
                    }
                });
                
                // Update any aria-labelledby or aria-describedby references
                const ariaElements = document.querySelectorAll('[aria-labelledby*="' + duplicateId + '"], [aria-describedby*="' + duplicateId + '"]');
                ariaElements.forEach(function(ariaEl) {
                    const attr = ariaEl.getAttribute('aria-labelledby') ? 'aria-labelledby' : 'aria-describedby';
                    const value = ariaEl.getAttribute(attr);
                    if (value && value.includes(duplicateId)) {
                        ariaEl.setAttribute(attr, value.replace(duplicateId, newId));
                    }
                });
            });
        });
        
        // Console log removed - no user-facing message needed for duplicate ID fix
        // This is a background fix that shouldn't clutter console
    }
    
    // Run on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', fixDuplicateIds);
    } else {
        fixDuplicateIds();
    }
    
    // Also run after dynamic content loads (for HTMX, AJAX, etc.)
    document.body.addEventListener('htmx:afterSwap', fixDuplicateIds);
    document.body.addEventListener('htmx:afterSettle', fixDuplicateIds);
})();

