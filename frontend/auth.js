document.addEventListener('DOMContentLoaded', () => {
    const authForm = document.getElementById('auth-form');
    const usernameInput = document.getElementById('username');
    const passwordInput = document.getElementById('password');
    const submitBtn = document.getElementById('submit-btn');
    const toggleLink = document.getElementById('toggle-link');
    const authTitle = document.getElementById('auth-title');
    const authSubtitle = document.getElementById('auth-subtitle');
    const errorMsg = document.getElementById('error-msg');
    const toggleText = document.getElementById('toggle-text');

    let isLogin = true;

    // Redirect if already logged in
    if (localStorage.getItem('lms_token')) {
        window.location.href = 'index.html';
    }

    toggleLink.addEventListener('click', () => {
        isLogin = !isLogin;
        errorMsg.style.display = 'none';

        if (isLogin) {
            authTitle.textContent = 'Welcome Back';
            authSubtitle.textContent = 'Sign in to continue to LMSBot';
            submitBtn.textContent = 'Sign In';
            toggleText.textContent = "Don't have an account? ";
            toggleLink.textContent = 'Sign Up';
        } else {
            authTitle.textContent = 'Create Account';
            authSubtitle.textContent = 'Sign up to get started';
            submitBtn.textContent = 'Sign Up';
            toggleText.textContent = 'Already have an account? ';
            toggleLink.textContent = 'Sign In';
        }
    });

    authForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const username = usernameInput.value.trim();
        const password = passwordInput.value.trim();

        if (!username || !password) {
            showError('Please fill in all fields');
            return;
        }

        const endpoint = isLogin ? '/login' : '/register';
        const url = endpoint; // Use relative path

        try {
            submitBtn.disabled = true;
            submitBtn.textContent = 'Processing...';

            const response = await fetch(url, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.message || 'Authentication failed');
            }

            if (isLogin) {
                localStorage.setItem('lms_token', data.token);
                localStorage.setItem('lms_user', username);
                window.location.href = 'index.html';
            } else {
                // Auto login after register or ask to sign in? 
                // Let's switch to login mode for better UX or auto-login logic
                showError('Registration successful! Please sign in.', 'green');
                toggleLink.click();
            }

        } catch (err) {
            showError(err.message);
        } finally {
            submitBtn.disabled = false;
            submitBtn.textContent = isLogin ? 'Sign In' : 'Sign Up';
        }
    });

    function showError(message, color = '#ff4444') {
        errorMsg.textContent = message;
        errorMsg.style.color = color;
        errorMsg.style.display = 'block';
    }
});
