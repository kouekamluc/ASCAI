// Event Management JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Handle registration form submission with confirmation
    const registrationForms = document.querySelectorAll('.registration-form');
    registrationForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const submitButton = form.querySelector('button[type="submit"]');
            if (submitButton) {
                const isWaitlist = submitButton.textContent.trim().includes('Waitlist');
                if (isWaitlist) {
                    if (!confirm('This event is full. You will be added to the waitlist. Continue?')) {
                        e.preventDefault();
                    }
                }
            }
        });
    });

    // Format datetime-local inputs
    const datetimeInputs = document.querySelectorAll('input[type="datetime-local"]');
    datetimeInputs.forEach(input => {
        // Ensure proper format for datetime-local
        if (input.value) {
            // Convert ISO format to datetime-local format if needed
            const date = new Date(input.value);
            if (!isNaN(date.getTime())) {
                const year = date.getFullYear();
                const month = String(date.getMonth() + 1).padStart(2, '0');
                const day = String(date.getDate()).padStart(2, '0');
                const hours = String(date.getHours()).padStart(2, '0');
                const minutes = String(date.getMinutes()).padStart(2, '0');
                input.value = `${year}-${month}-${day}T${hours}:${minutes}`;
            }
        }
    });
});











