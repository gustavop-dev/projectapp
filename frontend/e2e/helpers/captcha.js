/** Google is the sole simulated boundary; the app still submits real tokens. */
export async function mockCaptchaProvider(page, testId, { mode = 'valid', failScript = false } = {}) {
  await page.route('https://www.google.com/recaptcha/api.js*', async (route) => {
    if (failScript) return route.abort('failed')
    const callback = new URL(route.request().url()).searchParams.get('onload')
    await route.fulfill({
      contentType: 'application/javascript',
      body: `(() => {
        let counter = 0;
        const widgets = [];
        window.grecaptcha = {
          render(container, options) {
            const target = typeof container === 'string' ? document.getElementById(container) : container;
            const label = document.createElement('label');
            const box = document.createElement('input');
            box.type = 'checkbox';
            label.append(box, 'No soy un robot (prueba)');
            const token = document.createElement('input');
            token.type = 'hidden'; token.name = 'g-recaptcha-response';
            const expire = document.createElement('button');
            expire.type = 'button'; expire.textContent = 'Expirar verificación (prueba)';
            expire.onclick = () => { box.checked = false; token.value = ''; options['expired-callback'](); };
            box.onchange = () => {
              token.value = ${JSON.stringify(`${mode}-${testId}-`)} + (++counter);
              options.callback(token.value);
            };
            target.append(label, token, expire);
            widgets.push({box, token}); return widgets.length - 1;
          },
          reset(id) { widgets[id].box.checked = false; widgets[id].token.value = ''; }
        };
        window[${JSON.stringify(callback)}]();
      })();`,
    })
  })
}

export const captchaCredentials = {
  email: 'browser-captcha@example.com',
  password: 'Browser-test-password-1',
}
