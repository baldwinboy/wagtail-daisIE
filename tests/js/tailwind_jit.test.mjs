import assert from 'node:assert/strict';
import test from 'node:test';

import {
    CssStreamBuffer,
    apiHeaders,
    compileMessage,
    parseConfig,
    validateCss,
} from '../../src/wagtail_daisIE/static/wagtail_daisIE/js/tailwind_jit.js';

test('validateCss accepts structural CSS', () => {
    assert.equal(validateCss('.a { color: red; }'), '.a { color: red; }');
    assert.equal(
        validateCss(
            "@layer theme, base, components, utilities;\n@import 'tailwindcss/theme.css' layer(theme);",
        ),
        "@layer theme, base, components, utilities;\n@import 'tailwindcss/theme.css' layer(theme);",
    );
});

test('validateCss rejects unsafe or malformed CSS', () => {
    for (const css of [
        '',
        '.a { color: red;',
        '.a { content: "<script>"; }',
        '.a { content: "</style>"; }',
        '.a { color: red; }\0',
    ]) {
        assert.throws(() => validateCss(css));
    }
});

test('CssStreamBuffer flushes complete statements', () => {
    const buffer = new CssStreamBuffer();
    assert.equal(buffer.append('.a { color: red;'), '');
    assert.equal(buffer.append(' }'), '.a { color: red; }');
    assert.equal(buffer.flush(), '');
});

test('CssStreamBuffer rejects incomplete final CSS', () => {
    const buffer = new CssStreamBuffer();
    buffer.append('.a {');
    assert.throws(() => buffer.flush());
});

test('apiHeaders contains no nonce', () => {
    assert.deepEqual(apiHeaders(), {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
    });
});

test('compileMessage contains no nonce', () => {
    assert.deepEqual(JSON.parse(compileMessage('.a { color: red; }')), {
        type: 'compile',
        stylesheet: '.a { color: red; }',
    });
});

test('parseConfig reads JSON config elements', () => {
    const element = { textContent: '{"mode":"fetch","cssUrl":"/x.css"}' };
    assert.deepEqual(parseConfig(element), {
        mode: 'fetch',
        cssUrl: '/x.css',
    });
    assert.equal(parseConfig({ textContent: 'not json' }), null);
    assert.equal(parseConfig(null), null);
});
