import assert from 'node:assert/strict';
import test from 'node:test';

import '../../src/wagtail_daisIE/static/wagtail_daisIE/js/feed_title_slug.js';

const { slugify, attach } = globalThis.daisieFeedTitleSlug;

function input(value = '') {
  const listeners = new Map();
  return {
    value,
    addEventListener(type, fn) {
      if (!listeners.has(type)) listeners.set(type, []);
      listeners.get(type).push(fn);
    },
    removeEventListener(type, fn) {
      const list = listeners.get(type);
      if (!list) return;
      const index = list.indexOf(fn);
      if (index !== -1) list.splice(index, 1);
    },
    emit(type) {
      const list = listeners.get(type) || [];
      list.forEach((fn) => fn());
    },
    listenerCount(type) {
      return (listeners.get(type) || []).length;
    },
  };
}

test('slugify normalises a title', () => {
  assert.equal(slugify('My Feed'), 'my-feed');
  assert.equal(slugify('  Multiple   spaces  '), 'multiple-spaces');
  assert.equal(slugify('Café & Brunch'), 'cafe-brunch');
  assert.equal(slugify('Already_slug'), 'already-slug');
  assert.equal(slugify(''), '');
  assert.equal(slugify('!!!'), '');
});

test('attach fills an empty name from the title', () => {
  const source = input('My Feed');
  const target = input('');
  attach(source, target);
  assert.equal(target.value, 'my-feed');
});

test('attach keeps updating while the name is untouched', () => {
  const source = input('My Feed');
  const target = input('');
  attach(source, target);
  source.value = 'New Title';
  source.emit('input');
  assert.equal(target.value, 'new-title');
});

test('attach stops after the name is edited', () => {
  const source = input('My Feed');
  const target = input('');
  attach(source, target);
  target.value = 'custom-name';
  target.emit('input');
  source.value = 'Another Title';
  source.emit('input');
  assert.equal(target.value, 'custom-name');
});

test('attach treats an existing name as manually edited', () => {
  const source = input('Title');
  const target = input('custom');
  attach(source, target);
  source.value = 'Other Title';
  source.emit('input');
  assert.equal(target.value, 'custom');
});

test('attach does not clear the name when the title is empty', () => {
  const source = input('');
  const target = input('existing-name');
  attach(source, target);
  assert.equal(target.value, 'existing-name');
  source.value = 'New Title';
  source.emit('input');
  assert.equal(target.value, 'existing-name');
});

test('attach cleanup removes listeners', () => {
  const source = input('My Feed');
  const target = input('');
  const cleanup = attach(source, target);
  assert.equal(target.value, 'my-feed');
  cleanup();
  assert.equal(source.listenerCount('input'), 0);
  assert.equal(target.listenerCount('input'), 0);
  source.value = 'Changed';
  source.emit('input');
  assert.equal(target.value, 'my-feed');
});
