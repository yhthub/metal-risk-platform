import test from 'node:test'
import assert from 'node:assert/strict'
import { controlSources, pathways, selectPathways } from '../app/utils/causalEvidence.ts'

test('only complete metal sets match and unreleased outcomes have no evidence', () => {
  assert.deepEqual(selectPathways([], 'renal'), [])
  assert.deepEqual(selectPathways(['Hg'], 'renal'), [])
  assert.deepEqual(selectPathways(['Pb', 'Cd', 'Hg'], 'unsupported'), [])
  assert.deepEqual(selectPathways(['Cd'], 'sbp'), [])
  const lead = selectPathways(['Pb'], 'renal')
  assert.ok(lead.length)
  assert.ok(lead.every(p => p.kind === 'single' && p.metals.length === 1))
  assert.deepEqual(selectPathways(['Pb', 'Hg', 'Pb'], 'renal'), lead)
  assert.deepEqual(selectPathways(['Pb', 'Cd'], 'sbp'), selectPathways(['Pb'], 'sbp'))
})

test('the same joint study reports different interaction results for its two endpoints', () => {
  const selected = selectPathways(['Cd', 'Pb'], 'renal')
  assert.deepEqual(selected, selectPathways(['Pb', 'Cd', 'Cd'], 'renal'))
  const joint = selected.filter(pathway => pathway.kind === 'joint')
  const albumin = joint.find(pathway => pathway.id === 'pb-cd-albuminuria')
  const egfr = joint.find(pathway => pathway.id === 'pb-cd-egfr')
  assert.ok(albumin && egfr)
  assert.equal(albumin.source.url, egfr.source.url)
  assert.match(albumin.observed, /P = 0\.003/)
  assert.match(egfr.observed, /P = 0\.17/)
})

test('the cadmium cell experiment remains separate from human follow-up findings', () => {
  const selected = selectPathways(['Cd'], 'renal')
  const mechanism = selected.find(pathway => pathway.kind === 'mechanism')
  const followup = selected.find(pathway => pathway.id === 'cd-proximal-tubule')
  assert.ok(mechanism && followup)
  assert.match(mechanism.summary, /LLC-PK1/)
  assert.equal(followup.kind, 'single')
  assert.notEqual(mechanism.source.url, followup.source.url)
})

test('evidence selection never returns an occupational control as a medical observation', () => {
  assert.equal(new Set([...pathways, ...controlSources].map(entry => entry.id)).size, pathways.length + controlSources.length)
  assert.deepEqual(new Set(controlSources.flatMap(control => control.metals)), new Set(['Pb', 'Cd']))
  for (const entry of [...pathways, ...controlSources]) {
    assert.equal(new URL(entry.source.url).protocol, 'https:')
    assert.ok(entry.source.issuer && entry.source.title && entry.source.locator && entry.source.year)
  }
  for (const control of controlSources) {
    assert.ok(control.label && control.text)
    assert.ok(selectPathways(control.metals, 'renal').every(entry => entry.id !== control.id))
  }
})
