import test from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'
import path from 'node:path'
import vm from 'node:vm'
import { createRequire } from 'node:module'
import { fileURLToPath } from 'node:url'
import * as vue from 'vue'
import { renderRagMarkdown } from '../app/utils/ragMarkdown.ts'

// Exact excerpt of the Chinese live response recorded on 2026-11-09.
// These tests check rendering only, not the medical validity of the response.
const liveAnswerExcerpt = `## 镉暴露与肾损伤的关系

**所给摘录支持：镉暴露与肾损伤指标异常有关，尤其是肾近端小管功能异常；但这些材料不能证明低水平镉暴露必然导致慢性肾病。**[E1][E2]

### 局限与未知
- E1样本较小、限于特定老年人群，且摘要末尾截断，不能判断其余肾损伤指标的完整结果。[E1]
- E3虽标注为“guidelines”，正文主要介绍铅—镉共同暴露研究的方法，没有完整结果，**不能作为已核实的指南推荐，也不能据此分离镉的独立作用**。[E3]`

const buttonIds = html => [...html.matchAll(/<button\b[^>]*data-citation-id="(E\d+)"/g)].map(match => match[1])

test('real answer renders headings, emphasis, lists and only supplied references', () => {
  const html = renderRagMarkdown(liveAnswerExcerpt, ['E1', 'E2', 'E3'])
  assert.match(html, /<h2>镉暴露与肾损伤的关系<\/h2>/)
  assert.match(html, /<h3>局限与未知<\/h3>/)
  assert.match(html, /<strong>所给摘录支持：/)
  assert.match(html, /<ul>\s*<li>/)
  assert.deepEqual(buttonIds(html), ['E1', 'E2', 'E1', 'E3'])
  assert.match(html, /不能作为已核实的指南推荐/)
})

test('Chinese colon labels adjoining Chinese prose render as strong without changing the prose', () => {
  // The live answer used this label immediately before its first sentence.
  const html = renderRagMarkdown('- **人体观察性研究：**一项先导研究纳入153名长期居住于中度镉污染地区、年龄≥60岁的非吸烟者。[E1]\n- **综述证据：**综述内容。\n- **局限:**尚有未知。', ['E1'])
  assert.match(html, /<strong>人体观察性研究：<\/strong>一项先导研究纳入153名/)
  assert.match(html, /<strong>综述证据：<\/strong>综述内容。/)
  assert.match(html, /<strong>局限:<\/strong>尚有未知。/)
  assert.deepEqual(buttonIds(html), ['E1'])
})

test('Chinese sentence emphasis adjoining Chinese prose preserves the live answer text', () => {
  const examples = [
    ['铅暴露与血压升高、高血压风险增加有关，尤其需要关注长期、累积暴露。', '但这不意味着…'],
    ['低水平暴露也值得重视，但其影响大小并非在所有研究中一致。', '低水平暴露…'],
    ['排版样例'.repeat(30) + '。', '后续正文'],
  ]
  for (const [sentence, following] of examples) {
    assert.equal(renderRagMarkdown(`**${sentence}**${following}`),
      `<p><strong>${sentence}</strong>${following}</p>\n`)
  }
  assert.equal(renderRagMarkdown('**观察证据。**正文**尚有局限。**补充'),
    '<p><strong>观察证据。</strong>正文<strong>尚有局限。</strong>补充</p>\n')
})

test('Chinese sentence compatibility respects code, links, escapes and emphasis boundaries', () => {
  const examples = [
    '`**观察证据。**正文`',
    '```text\n**观察证据。**正文\n```',
    '[**观察证据。**正文 [E1]](https://example.org)',
    String.raw`\*\*观察证据。**正文`,
    String.raw`**观察证据。\*\*正文`,
    '**观察证据。****尚有局限。**正文',
    '**观察证据。\n尚有局限。**正文',
    '**观察证据。\n\n尚有局限。**正文',
    '**中文<script>。**正文',
    '**中文句子。**English',
  ]
  for (const source of examples) {
    assert.doesNotMatch(renderRagMarkdown(source, ['E1']), /<(?:strong|script|button)\b/, source)
  }
  assert.equal(renderRagMarkdown('**观察证据。****尚有局限。**正文'),
    '<p>**观察证据。****尚有局限。**正文</p>\n')
  assert.equal(renderRagMarkdown('**观察证据。\n\n尚有局限。**正文'),
    '<p>**观察证据。</p>\n<p>尚有局限。**正文</p>\n')
})

test('Chinese label compatibility does not reinterpret code, links, escapes or broader markup', () => {
  const html = renderRagMarkdown('`**综述证据：**综述`\n\n```text\n**综述证据：**综述\n```\n\n[**综述证据：**综述 [E1]](https://example.org)\n\n\\*\\*综述证据：\\*\\*综述\n\n**Evidence:**正文\n\n**中文标签：**English\n\n**中文<script>：**正文\n\n**未闭合：正文', ['E1'])
  assert.match(html, /<code>\*\*综述证据：\*\*综述<\/code>/)
  assert.match(html, /<pre><code class="language-text">\*\*综述证据：\*\*综述/)
  assert.match(html, /<a [^>]*>\*\*综述证据：\*\*综述 \[E1\]<\/a>/)
  assert.match(html, /<p>\*\*综述证据：\*\*综述<\/p>/)
  assert.match(html, /\*\*Evidence:\*\*正文/)
  assert.match(html, /\*\*中文标签：\*\*English/)
  assert.match(html, /&lt;script&gt;/)
  assert.doesNotMatch(html, /<(?:strong|script|button)\b/)
})

test('standard tables, numbered lists, quotes and code preserve their structure', () => {
  const html = renderRagMarkdown(`| 项目 | 内容 |
| --- | --- |
| 样例 | **说明** |

1. 第一项
2. 第二项

> 仅用于排版测试。

\`inline <tag>\`

\`\`\`html
<script>alert(1)</script>
\`\`\``)
  assert.match(html, /<table>/)
  assert.match(html, /<th>项目<\/th>/)
  assert.match(html, /<td><strong>说明<\/strong><\/td>/)
  assert.match(html, /<ol>\s*<li>第一项/)
  assert.match(html, /<blockquote>/)
  assert.match(html, /<code>inline &lt;tag&gt;<\/code>/)
  assert.match(html, /<pre><code class="language-html">&lt;script&gt;/)
  assert.doesNotMatch(html, /<script\b/i)
})

test('raw HTML and encoded HTML are text, never executable markup', () => {
  const html = renderRagMarkdown(`<script>alert(document.cookie)</script>
<img src=x onerror=alert(1)>
<svg onload=alert(1)><a href="javascript:alert(1)">x</a></svg>
<iframe src="https://tracker.invalid"></iframe>
<button class="rag-citation" data-citation-id="E1" onclick="alert(1)">fake</button>
&lt;img src=x onerror=alert(1)&gt;`, ['E1'])
  assert.doesNotMatch(html, /<(?:script|img|svg|iframe|button|a)\b/i)
  assert.match(html, /&lt;script&gt;/)
  assert.deepEqual(buttonIds(html), [])
})

test('unsafe, local, obfuscated and protocol-relative links never become anchors', () => {
  const urls = [
    'javascript:alert%281%29', 'JaVaScRiPt:alert%281%29',
    'javascript&#x3A;alert%281%29', 'java&#x09;script:alert%281%29',
    'data:text/html;base64,PHNjcmlwdD4=', 'vbscript:msgbox%281%29',
    'file:///C:/private.txt', '//tracker.invalid/path', '/admin',
    'mailto:someone@example.com', 'javascript%3Aalert%281%29',
  ]
  for (const url of urls) {
    const html = renderRagMarkdown(`[click](${url})`)
    assert.doesNotMatch(html, /<a\b/i, url)
  }
  assert.doesNotMatch(renderRagMarkdown('[click][x]\n\n[x]: javascript:alert%281%29'), /<a\b/i)
})

test('external links are escaped and isolate the new browsing context', () => {
  const html = renderRagMarkdown('[source](https://example.org/evidence?a=1&b=2 "a & b") and <https://example.org>')
  assert.match(html, /href="https:\/\/example.org\/evidence\?a=1&amp;b=2"/)
  assert.match(html, /title="a &amp; b"/)
  assert.equal((html.match(/target="_blank" rel="noopener noreferrer"/g) || []).length, 2)
  assert.doesNotMatch(renderRagMarkdown('[x](https://example.org/ "x\" onclick=\"alert(1)")'), /\sonclick="/i)
})

test('images never load, including linked images, data images and raw HTML', () => {
  const html = renderRagMarkdown(`![remote](https://tracker.invalid/pixel.png)
[![linked [E1]](https://tracker.invalid/second.png)](https://example.org)
![embedded](data:image/png;base64,AAAA)
<img src="https://tracker.invalid/raw.png">`, ['E1'])
  assert.doesNotMatch(html, /<(?:img|picture|source|svg|iframe)\b/i)
  assert.match(html, /<span class="rag-image-alt">remote<\/span>/)
  assert.match(html, /linked \[E1\]/)
  assert.deepEqual(buttonIds(html), [])
  assert.doesNotMatch(html, /(?:src|srcset)="https:/)
})

test('citations are exact allowlisted text tokens, outside code and links', () => {
  const html = renderRagMarkdown(`正文 [E1] [E2] [E99] [ordinary] [E0] [E01]

**[E1]** and [source [E1]](https://example.org)

\`[E1]\`

\`\`\`text
[E1]
\`\`\`

    [E1]

| 资料 |
| --- |
| [E2] |`, ['E1', 'E2', 'E01', 'E0', 'E1" onclick="alert(1)'])
  assert.deepEqual(buttonIds(html), ['E1', 'E2', 'E1', 'E2'])
  assert.match(html, /\[E99\] \[ordinary\] \[E0\] \[E01\]/)
  assert.match(html, /<a [^>]*>source \[E1\]<\/a>/)
  assert.match(html, /<code>\[E1\]<\/code>/)
  assert.match(html, /<pre><code class="language-text">\[E1\]/)
  assert.match(html, /<pre><code>\[E1\]/)
  assert.doesNotMatch(html, /\sonclick=/)
})

test('no citation buttons by default, and allowlists do not leak between renders', () => {
  assert.deepEqual(buttonIds(renderRagMarkdown('[E1]')), [])
  assert.deepEqual(buttonIds(renderRagMarkdown('[E1]', ['E1'])), ['E1'])
  assert.deepEqual(buttonIds(renderRagMarkdown('[E1] [E2]', ['E2'])), ['E2'])
  // Legacy combined notation is left intact; the backend owns normalization/validation.
  assert.deepEqual(buttonIds(renderRagMarkdown('[E1, E4, E5] [E1–E5]', ['E1', 'E4', 'E5'])), [])
})

const require = createRequire(import.meta.url)
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
const pnpm = path.join(root, 'node_modules/.pnpm')
const dependency = (prefix, name) => require(path.join(pnpm, fs.readdirSync(pnpm).find(item => item.startsWith(prefix)), 'node_modules', name))
const ts = dependency('typescript@', 'typescript')
const compiler = dependency('@vue+compiler-sfc@', '@vue/compiler-sfc')
const { renderToString } = dependency('@vue+server-renderer@', '@vue/server-renderer')
const filename = path.join(root, 'app/components/RagAnswer.vue')
const source = fs.readFileSync(filename, 'utf8')
const parsed = compiler.parse(source, { filename })
assert.deepEqual(parsed.errors, [])
const script = compiler.compileScript(parsed.descriptor, { id: 'rag-answer-test', inlineTemplate: true })

// Minimal Element objects exercise the component's actual delegated click handler.
class TestElement {
  constructor(id) { this.dataset = { citationId: id }; this.button = null; this.contained = null }
  closest() { return this.button }
  contains(element) { return element === this.contained }
}
const runtime = { exports: {} }
vm.runInNewContext(ts.transpileModule(script.content, {
  compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.CommonJS },
}).outputText, {
  exports: runtime.exports, module: runtime, Element: TestElement,
  require: name => {
    if (name === 'vue') return vue
    assert.equal(name, '../utils/ragMarkdown')
    return { renderRagMarkdown }
  },
})
const component = runtime.exports.default

test('RagAnswer SFC compiles and SSR renders safe parsed content with default empty citations', async () => {
  assert.deepEqual(compiler.compileStyle({ source: parsed.descriptor.styles[0].content, filename, id: 'rag-answer-test', scoped: true }).errors, [])
  const html = await renderToString(vue.createSSRApp(component, { content: '**answer** [E1] <script>x</script>' }))
  assert.match(html, /<strong>answer<\/strong>/)
  assert.match(html, /\[E1\] &lt;script&gt;/)
  assert.doesNotMatch(html, /<(?:script|button)\b/)
  const cited = await renderToString(vue.createSSRApp(component, { content: '[E1]', citationIds: ['E1'] }))
  assert.deepEqual(buttonIds(cited), ['E1'])
})

test('component emits only a valid citation button inside its own container', () => {
  const emitted = []
  const render = component.setup({ content: '[E1]', citationIds: ['E1'] }, {
    expose() {}, emit: (...args) => emitted.push(args),
  })
  const vnode = render({}, [])
  const container = new TestElement()
  const target = new TestElement()
  const button = new TestElement('E1')
  target.button = button
  container.contained = button
  vnode.props.onClick({ target, currentTarget: container })
  assert.deepEqual(emitted, [['citation', 'E1']])
  button.dataset.citationId = 'E99'
  vnode.props.onClick({ target, currentTarget: container })
  button.dataset.citationId = 'E1'
  container.contained = null
  vnode.props.onClick({ target, currentTarget: container })
  vnode.props.onClick({ target: {}, currentTarget: container })
  assert.equal(emitted.length, 1)
})
