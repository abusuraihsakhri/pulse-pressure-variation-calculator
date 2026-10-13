import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';

const html = readFileSync(new URL('../index.html', import.meta.url), 'utf8');
const script = html.match(/<script>([\s\S]*?)<\/script>/)?.[1];

test('homepage has a valid embedded calculator and no external scripts', () => {
  assert.ok(script, 'Expected local inline calculator script');
  assert.doesNotThrow(() => new vm.Script(script));
  assert.doesNotMatch(html, /<script[^>]+src=/i);
  assert.match(html, /Pulse Pressure Variation Calculator/);
});

function app() {
  const ids = ['calculator', 'mode', 'pp-max', 'pp-min', 'sbp-max', 'dbp-max',
    'sbp-min', 'dbp-min', 'pulse-fields', 'paired-fields', 'error', 'empty',
    'result', 'ppv', 'max-out', 'min-out', 'mean-out', 'example', 'download'];
  const els = Object.fromEntries(ids.map((id) => [id, {
    value: '', hidden: false, textContent: '', listeners: {},
    addEventListener(name, fn) { this.listeners[name] = fn; },
    fire(name) { this.listeners[name]?.({ preventDefault() {} }); },
  }]));
  els.mode.value = 'pulse';
  const downloads = [];
  const context = {
    document: {
      getElementById: (id) => els[id],
      createElement: () => ({
        click() { downloads.push(this.download); },
        remove() {},
      }),
      body: { appendChild() {} },
    },
    Blob,
    URL: { createObjectURL: () => 'blob:local-test', revokeObjectURL() {} },
  };
  vm.runInNewContext(script, context);
  return { els, downloads };
}

test('pulse-pressure mode calculates and exports', () => {
  const { els, downloads } = app();
  els['pp-max'].value = '42';
  els['pp-min'].value = '38';
  els.calculator.fire('submit');
  assert.equal(els.ppv.textContent, '10.00');
  assert.equal(els['mean-out'].textContent, '40.00');
  assert.equal(els.result.hidden, false);
  els.download.fire('click');
  assert.deepEqual(downloads, ['pulse-pressure-variation.csv']);
});

test('paired pressures use same-beat values', () => {
  const { els } = app();
  els.mode.value = 'paired';
  els.mode.fire('change');
  assert.equal(els['paired-fields'].hidden, false);
  Object.assign(els['sbp-max'], {value: '122'});
  Object.assign(els['dbp-max'], {value: '80'});
  Object.assign(els['sbp-min'], {value: '118'});
  Object.assign(els['dbp-min'], {value: '80'});
  els.calculator.fire('submit');
  assert.equal(els.ppv.textContent, '10.00');
});

test('invalid, missing and stale measurements do not show a result', () => {
  const { els } = app();
  els['pp-max'].value = '38';
  els['pp-min'].value = '42';
  els.calculator.fire('submit');
  assert.match(els.error.textContent, /Maximum pulse pressure/);
  assert.equal(els.result.hidden, true);
  els['pp-max'].value = '42';
  els.calculator.fire('submit');
  assert.equal(els.ppv.textContent, '0.00');
  els['pp-max'].value = '';
  els['pp-max'].fire('input');
  assert.equal(els.result.hidden, true);
  els.calculator.fire('submit');
  assert.match(els.error.textContent, /required/);
  els.example.fire('click');
  assert.equal(els['pp-max'].value, '42');
});
