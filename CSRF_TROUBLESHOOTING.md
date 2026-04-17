# 🔒 CSRF Token Troubleshooting Guide

## 🚨 Common CSRF Issues & Solutions

### **What is CSRF?**
Cross-Site Request Forgery (CSRF) protection prevents malicious websites from submitting forms on your behalf.

### **Error Message:**
```
Forbidden (403)
CSRF verification failed. Request aborted.
CSRF token from POST incorrect.
```

## 🔧 **Common Causes & Solutions**

### **1. Browser Cookies Disabled**
**Problem**: Browser not accepting cookies
**Solution**:
- Enable cookies in your browser settings
- Allow cookies for `localhost` and `127.0.0.1`
- Check browser's cookie settings

### **2. Multiple Browser Tabs**
**Problem**: Multiple tabs with same session
**Solution**:
- Close other browser tabs
- Use single tab for form submission
- Refresh page before submitting

### **3. Session Timeout**
**Problem**: Session expired
**Solution**:
- Log out and log back in
- Refresh the page
- Submit form immediately after login

### **4. Browser Cache Issues**
**Problem**: Old cached form data
**Solution**:
- Clear browser cache and cookies
- Hard refresh (Ctrl+F5 or Cmd+Shift+R)
- Use incognito/private browsing mode

### **5. Development Server Issues**
**Problem**: Development server session issues
**Solution**:
- Restart Django development server
- Clear browser data
- Try different browser

## 🛠️ **Technical Solutions**

### **For Developers:**

#### **1. Check CSRF Middleware**
Ensure CSRF middleware is enabled in `settings.py`:
```python
MIDDLEWARE = [
    'django.middleware.csrf.CsrfViewMiddleware',
    # ... other middleware
]
```

#### **2. Verify Template Tags**
All POST forms must include `{% csrf_token %}`:
```html
<form method="post">
    {% csrf_token %}
    <!-- form fields -->
</form>
```

#### **3. Check View Decorators**
Views using POST should have proper decorators:
```python
from django.views.decorators.csrf import csrf_protect

@csrf_protect
def my_view(request):
    # view logic
```

#### **4. AJAX Requests**
For AJAX requests, include CSRF token in headers:
```javascript
// Get CSRF token
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Include in AJAX headers
const csrftoken = getCookie('csrftoken');
fetch('/api/endpoint/', {
    method: 'POST',
    headers: {
        'X-CSRFToken': csrftoken,
        'Content-Type': 'application/json',
    },
    body: JSON.stringify(data)
});
```

## 🚀 **Quick Fixes**

### **Immediate Solutions:**

#### **1. Refresh Page**
- Press `Ctrl+F5` (Windows/Linux) or `Cmd+Shift+R` (Mac)
- This reloads page without cache

#### **2. Clear Browser Data**
- Clear cookies and cache
- Restart browser
- Try again

#### **3. Use Different Browser**
- Try Chrome, Firefox, or Safari
- Some browsers have stricter security policies

#### **4. Restart Development Server**
```bash
# Stop server (Ctrl+C)
python manage.py runserver
```

#### **5. Check Form Structure**
Ensure your form has:
```html
<form method="post">
    {% csrf_token %}
    <!-- form fields -->
    <button type="submit">Submit</button>
</form>
```

## 🔍 **Debugging Steps**

### **1. Check Browser Console**
- Open Developer Tools (F12)
- Look for JavaScript errors
- Check Network tab for failed requests

### **2. Verify CSRF Token**
- View page source
- Search for `csrfmiddlewaretoken`
- Ensure token is present

### **3. Check Session Data**
```python
# In Django shell
python manage.py shell
>>> from django.contrib.sessions.models import Session
>>> Session.objects.all()
```

### **4. Test with Simple Form**
Create a simple test form:
```html
<form method="post">
    {% csrf_token %}
    <input type="text" name="test">
    <button type="submit">Test</button>
</form>
```

## 🛡️ **Security Best Practices**

### **For Production:**
- Use HTTPS
- Set secure cookie flags
- Configure proper CORS settings
- Monitor CSRF failures

### **For Development:**
- Keep DEBUG=True for detailed errors
- Use localhost for development
- Test in multiple browsers
- Clear cache regularly

## 📱 **Mobile-Specific Issues**

### **Mobile Browser CSRF Problems:**
- Clear mobile browser data
- Check mobile browser settings
- Try desktop browser for comparison
- Ensure mobile browser accepts cookies

## 🎯 **HMS-Specific Solutions**

### **Registration Form CSRF Issues:**

#### **1. Simple Registration**
- URL: `/accounts/simple-register/`
- Form has CSRF token ✅
- Auto-login after registration

#### **2. Profile Edit**
- URL: `/accounts/profile/edit/`
- Form has CSRF token ✅
- Role-specific forms

#### **3. Appointment Booking**
- URL: `/appointments/book_appointment/`
- Form has CSRF token ✅
- Proper validation

## 🚨 **When to Contact Support**

If you've tried all solutions and still get CSRF errors:

1. **Document the Issue**:
   - What form are you submitting?
   - What browser are you using?
   - What error message appears?
   - Steps to reproduce

2. **Check System Status**:
   - Is Django server running?
   - Are there any server errors?
   - Are cookies enabled?

3. **Provide Context**:
   - Recent changes to code
   - Browser version
   - Network environment

## 📞 **Quick Help**

### **Immediate Actions:**
1. **Refresh page** (Ctrl+F5)
2. **Clear browser cache**
3. **Restart development server**
4. **Try different browser**
5. **Check form has `{% csrf_token %}`

---

**🔒 Most CSRF issues are resolved with a simple page refresh!** 

If problems persist, the issue is likely with browser settings or session management rather than the code itself.
