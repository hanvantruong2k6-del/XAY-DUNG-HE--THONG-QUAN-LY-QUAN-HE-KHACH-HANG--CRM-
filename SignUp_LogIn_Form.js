const form = document.getElementById('loginForm');
const pw = document.getElementById('password');
const eye = document.getElementById('eye');
const err = document.getElementById('error');
const btn = document.getElementById('btn');

// Nút hiện/ẩn mật khẩu
eye.addEventListener('click', () => {
    const show = pw.type === 'password';
    pw.type = show ? 'text' : 'password';
    eye.className = (show ? 'bx bx-hide' : 'bx bx-show') + ' toggle-eye';
});

document.getElementById('forgot').addEventListener('click', (e) => {
    e.preventDefault();
    alert('Vui lòng liên hệ quản trị viên để được cấp lại mật khẩu.');
});

// Gửi đăng nhập tới server C++
form.addEventListener('submit', async (e) => {
    e.preventDefault();
    err.textContent = '';
    btn.disabled = true;
    try {
        const res = await fetch('/api/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username: form.username.value.trim(), password: pw.value })
        });
        const data = await res.json();
        if (data.ok) {
            location.href = '/dashboard.html';
        } else {
            err.textContent = data.message;
        }
    } catch {
        err.textContent = 'Không kết nối được máy chủ';
    } finally {
        btn.disabled = false;
    }
});

// Lời chào theo tên đang gõ (chỉ phản chiếu chữ vừa nhập, không kiểm tra tài khoản)
const welcome = document.getElementById('welcome');
form.username.addEventListener('input', () => {
    const name = form.username.value.trim();
    welcome.textContent = name ? 'Xin chào, ' + name : 'Chào mừng bạn quay trở lại';
});
