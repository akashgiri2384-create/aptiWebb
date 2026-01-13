// API Tester JavaScript
const accessToken = localStorage.getItem('access_token');
const user = JSON.parse(localStorage.getItem('user') || '{}');
let currentAttemptId = null;
let currentQuizId = null;
let currentQuestionId = null;

// Check auth status
if (accessToken) {
    document.getElementById('auth-status').className = 'alert alert-success';
    document.getElementById('auth-message').textContent = `Authenticated as ${user.email}`;
} else {
    document.getElementById('auth-status').className = 'alert alert-warning';
    document.getElementById('auth-message').textContent = 'Not authenticated - some tests will fail';
}

// Test functions
const tests = {
    'register': async () => {
        const randomEmail = `test${Date.now()}@quizzy.com`;
        return fetch('/api/accounts/register/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                email: randomEmail,
                password: 'testpass123',
                full_name: 'API Test User',
                college_id: 'a2a2a2a2-a2a2-a2a2-a2a2-a2a2a2a2a2a2', // You'll need a real college ID
                accepted_terms: true,
                accepted_privacy: true
            })
        });
    },
    
    'login': async () => {
        return fetch('/api/accounts/login/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                email: 'test@quizzy.com',
                password: 'testpass123'
            })
        });
    },
    
    'profile': async () => {
        return fetch('/api/accounts/profile/', {
            headers: { 'Authorization': `Bearer ${accessToken}` }
        });
    },
    
    'update-profile': async () => {
        return fetch('/api/accounts/profile/update/', {
            method: 'PUT',
            headers: {
                'Authorization': `Bearer ${accessToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                bio: 'Updated via API test'
            })
        });
    },
    
    'sessions': async () => {
        return fetch('/api/accounts/sessions/', {
            headers: { 'Authorization': `Bearer ${accessToken}` }
        });
    },
    
    'colleges': async () => {
        return fetch('/api/accounts/colleges/');
    },
    
    'quizzes-list': async () => {
        const response = await fetch('/api/quizzes/');
        const data = await response.json();
        if (data.success && data.data.results && data.data.results.length > 0) {
            currentQuizId = data.data.results[0].id;
        }
        return new Response(JSON.stringify(data));
    },
    
    'quiz-detail': async () => {
        if (!currentQuizId) {
            await tests['quizzes-list']();
        }
        return fetch(`/api/quizzes/${currentQuizId}/`);
    },
    
    'start-quiz': async () => {
        if (!currentQuizId) {
            await tests['quizzes-list']();
        }
        const response = await fetch(`/api/quizzes/${currentQuizId}/start/`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${accessToken}` }
        });
        const data = await response.json();
        if (data.success) {
            currentAttemptId = data.data.attempt_id;
            if (data.data.questions && data.data.questions.length > 0) {
                currentQuestionId = data.data.questions[0].id;
            }
        }
        return new Response(JSON.stringify(data));
    },
    
    'save-answer': async () => {
        if (!currentAttemptId) {
            await tests['start-quiz']();
        }
        return fetch(`/api/quizzes/attempts/${currentAttemptId}/answer/`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${accessToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                question_id: currentQuestionId,
                selected_answer: 'A'
            })
        });
    },
    
    'submit-quiz': async () => {
        if (!currentAttemptId) {
            await tests['start-quiz']();
            await tests['save-answer']();
        }
        return fetch(`/api/quizzes/attempts/${currentAttemptId}/submit/`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${accessToken}` }
        });
    },
    
    'quiz-results': async () => {
        if (!currentAttemptId) {
            await tests['start-quiz']();
            await tests['submit-quiz']();
        }
        return fetch(`/api/quizzes/attempts/${currentAttemptId}/`, {
            headers: { 'Authorization': `Bearer ${accessToken}` }
        });
    },
    
    'user-attempts': async () => {
        if (!currentQuizId) {
            await tests['quizzes-list']();
        }
        return fetch(`/api/quizzes/${currentQuizId}/attempts/`, {
            headers: { 'Authorization': `Bearer ${accessToken}` }
        });
    },
    
    'quiz-stats': async () => {
        return fetch('/api/quizzes/stats/', {
            headers: { 'Authorization': `Bearer ${accessToken}` }
        });
    },
    
    'xp-stats': async () => {
        return fetch('/api/xp/stats/', {
            headers: { 'Authorization': `Bearer ${accessToken}` }
        });
    },
    
    'level-progress': async () => {
        return fetch('/api/xp/level-progress/', {
            headers: { 'Authorization': `Bearer ${accessToken}` }
        });
    },
    
    'badges': async () => {
        return fetch('/api/xp/badges/', {
            headers: { 'Authorization': `Bearer ${accessToken}` }
        });
    },
    
    'xp-logs': async () => {
        return fetch('/api/xp/logs/', {
            headers: { 'Authorization': `Bearer ${accessToken}` }
        });
    },
    
    'leaderboard': async () => {
        return fetch('/api/leaderboards/');
    },
    
    'quiz-leaderboard': async () => {
        if (!currentQuizId) {
            await tests['quizzes-list']();
        }
        return fetch(`/api/leaderboards/quiz/${currentQuizId}/`);
    },
    
    'college-leaderboard': async () => {
        return fetch('/api/leaderboards/colleges/');
    },
    
    'my-position': async () => {
        return fetch('/api/leaderboards/my-position/', {
            headers: { 'Authorization': `Bearer ${accessToken}` }
        });
    },
    
    'dashboard-stats': async () => {
        return fetch('/api/dashboard/stats/', {
            headers: { 'Authorization': `Bearer ${accessToken}` }
        });
    },
    
    'recent-activity': async () => {
        return fetch('/api/dashboard/activity/', {
            headers: { 'Authorization': `Bearer ${accessToken}` }
        });
    },
    
    'weekly-stats': async () => {
        return fetch('/api/dashboard/weekly/', {
            headers: { 'Authorization': `Bearer ${accessToken}` }
        });
    },
    
    'accuracy-trend': async () => {
        return fetch('/api/dashboard/accuracy-trend/', {
            headers: { 'Authorization': `Bearer ${accessToken}` }
        });
    },
    
    'today-quiz': async () => {
        return fetch('/api/daily-quizzes/today/', {
            headers: { 'Authorization': `Bearer ${accessToken}` }
        });
    },
    
    'unlock-quiz': async () => {
        return fetch('/api/daily-quizzes/unlock/', {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${accessToken}` }
        });
    },
    
    'watch-ad': async () => {
        return fetch('/api/daily-quizzes/watch-ad/', {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${accessToken}` }
        });
    },
    
    'key-balance': async () => {
        return fetch('/api/daily-quizzes/keys/', {
            headers: { 'Authorization': `Bearer ${accessToken}` }
        });
    },
    
    'admin-stats': async () => {
        return fetch('/api/admin-panel/stats/', {
            headers: { 'Authorization': `Bearer ${accessToken}` }
        });
    }
};

async function testAPI(testName) {
    const statusEl = document.getElementById(`status-${testName}`);
    statusEl.textContent = 'Testing...';
    statusEl.className = 'status status-pending';
    
    try {
        const response = await tests[testName]();
        const data = await response.json();
        
        const success = response.ok && (data.success !== false);
        
        statusEl.textContent = success ? '✓ Pass' : '✗ Fail';
        statusEl.className = success ? 'status status-success' : 'status status-error';
        
        addResult(testName, response.status, data, success);
    } catch (error) {
        statusEl.textContent = '✗ Error';
        statusEl.className = 'status status-error';
        addResult(testName, 0, { error: error.message }, false);
    }
}

function addResult(testName, status, data, success) {
    const resultsDiv = document.getElementById('results');
    const resultItem = document.createElement('div');
    resultItem.className = `result-item ${success ? '' : 'error'}`;
    
    resultItem.innerHTML = `
        <strong>${testName}</strong> - Status: ${status}
        <div class="json-preview">${JSON.stringify(data, null, 2)}</div>
    `;
    
    resultsDiv.insertBefore(resultItem, resultsDiv.firstChild);
}

function clearResults() {
    document.getElementById('results').innerHTML = '';
}

async function runAllTests() {
    const testNames = Object.keys(tests);
    for (const testName of testNames) {
        await testAPI(testName);
        await new Promise(resolve => setTimeout(resolve, 500)); // Delay between tests
    }
}
