// frontend/assets/google_auth.js
window.handleCredentialResponse = function(response) {
    // 1. Google gives us the secure JWT token
    const token = response.credential;
    
    // 2. Find the hidden Dash input field we created
    const hiddenInput = document.getElementById('google-auth-token');
    
    if (hiddenInput) {
        // 3. React/Dash trick to force update the value from external Javascript
        let nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set;
        nativeInputValueSetter.call(hiddenInput, token);
        
        // 4. Trigger an 'input' event so the Dash @callback fires immediately!
        let event = new Event('input', { bubbles: true });
        hiddenInput.dispatchEvent(event);
    }
};