<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import { rankBeans } from './beanMatching.js';
import BeanComparison from './components/BeanComparison.vue';
import AtlasHome from './components/AtlasHome.vue';
import BeanImage from './components/BeanImage.vue';
import SampleImageEditor from './components/SampleImageEditor.vue';
import FlavorExplorer from './components/FlavorExplorer.vue';

const view = ref(window.location.hash.slice(1) || 'home');
const loading = ref(true);
const errorMessage = ref('');
const categories = ref([]);
const tags = ref([]);
const coffees = ref([]);
const currentUser = ref(null);
const mobileNavOpen = ref(false);
const selectedFlavor = ref('');
const selectedCoffeeId = ref(null);
const compareIds = ref([]);
const comparisonFocusId = ref(null);
const adminImageSampleId = ref(null);
const searchQuery = ref('');
const countryFilter = ref('all');
const processFilter = ref('all');
const beanSearch = ref('');
const beanCountry = ref('all');
const beanProcess = ref('all');
const mapCountry = ref('');
const mapHoverCountry = ref('');
const mapViewBox = ref('0 0 920 500');
const mapSvg = ref(null);
const mapLandForms = ref([]);
const mapProjectionVersion = ref(0);
let worldProjection = null;
let mapAnimationFrame = null;
const modalCoffee = ref(null);
const reviews = ref([]);
const reviewSummary = ref({ count: 0, average: 0 });
const reviewForm = ref({ rating: 5, content: '' });
const reviewError = ref('');
const reviewBusy = ref(false);
const authMode = ref('login');
const authError = ref('');
const authBusy = ref(false);
const loginForm = ref({ username: '', password: '' });
const discovery = ref('bright');
const discoveryProcess = ref('all');
const discoveryRoast = ref('all');
const brew = ref({ dose: 18, water: 288, temperature: 92, time: 180 });
const extraction = ref({ dose: 18, beverage: 36, tds: 9.5 });
const brewTimerElapsed = ref(0);
const brewTimerRunning = ref(false);
let brewTimerInterval = null;
const converter = ref({ type: 'mass', value: 18 });
const cuppingForm = ref({ aroma: 7, acidity: 7, sweetness: 7, body: 7, aftertaste: 7, notes: '' });
const cuppingSaved = ref(false);
const adminSampleForm = ref({ name: '', country: 'China', region: '', species: 'Arabica', variety: '', process: '水洗', roast: '中浅烘', altitude: '', year: '2025', latitude: '', longitude: '', description: '' });
const adminTagForm = ref({ name: '', category: '', description: '' });
const adminError = ref('');
const adminBusy = ref(false);

const countryNames = {
  China: '中国', Ethiopia: '埃塞俄比亚', Panama: '巴拿马', Colombia: '哥伦比亚', Brazil: '巴西',
  Kenya: '肯尼亚', Indonesia: '印度尼西亚', 'Costa Rica': '哥斯达黎加', Rwanda: '卢旺达',
  Guatemala: '危地马拉', Honduras: '洪都拉斯', 'El Salvador': '萨尔瓦多', Nicaragua: '尼加拉瓜',
  Mexico: '墨西哥', Peru: '秘鲁', Bolivia: '玻利维亚', Ecuador: '厄瓜多尔', Tanzania: '坦桑尼亚',
  Uganda: '乌干达', Burundi: '布隆迪', India: '印度', Vietnam: '越南', 'Papua New Guinea': '巴布亚新几内亚',
  Yemen: '也门'
};

const countryMeta = {
  China: { name: '中国', intro: '中国咖啡以云南最具代表性，普洱、保山、德宏等地形成了稳定产区。杯中常见坚果、红糖、柔和果酸与可可感，新处理法也在提升果香层次。', note: '云南、普洱、保山', color: '#b8453f' },
  Ethiopia: { name: '埃塞俄比亚', intro: '咖啡风味叙事的核心产地之一。高海拔水洗样本常见茉莉、柑橘和茶感；日晒与厌氧则更容易把莓果和发酵甜感推出来。', note: '耶加雪菲、古吉、西达摩', color: '#7a68a6' },
  Panama: { name: '巴拿马', intro: '以波奎特和瑰夏闻名。花香、柑橘与精致核果感很突出，适合展示高端精品豆的层次和洁净度。', note: '波奎特、瑰夏、竞赛豆', color: '#d38e3d' },
  Colombia: { name: '哥伦比亚', intro: '产区跨度大、处理法丰富，是观察风味均衡度的好样本。常见柑橘、红糖、可可与温和核果结构，适合做对比基准。', note: '薇拉、考卡、安蒂奥基亚', color: '#cb5a43' },
  Brazil: { name: '巴西', intro: '世界最重要的商业与精品产地之一。低酸、厚实、坚果与可可感很常见，日晒和自然处理样本尤其适合讲拼配逻辑。', note: '米纳斯、圣保罗、黄波旁', color: '#927043' },
  Kenya: { name: '肯尼亚', intro: '高海拔水洗样本常带明显黑加仑、柑橘和明亮酸质。SL 系列品种与精细分级体系，让它很适合作为酸质范例。', note: '涅里、基安布、SL28', color: '#c16b3e' },
  Indonesia: { name: '印度尼西亚', intro: '湿刨处理非常有辨识度，杯中通常更厚、更深、更偏草本与香料。用来展示非洲系明亮风味之外的另一条路径很合适。', note: '苏门答腊、湿刨、曼特宁', color: '#5e7751' },
  'Costa Rica': { name: '哥斯达黎加', intro: '蜜处理和清洁度控制做得很成熟，甜感、柑橘和杏仁结构常常很平衡。适合讲清楚处理法如何改变风味轮廓。', note: '塔拉珠、蜜处理、清晰甜感', color: '#b46f3e' },
  Rwanda: { name: '卢旺达', intro: '高海拔小农模式下常出现莓果、红茶和红糖调性。厌氧和发酵型样本会把这一类国家的果感与甜感放得更明显。', note: '西部省、波旁、发酵表达', color: '#a24b63' },
  Guatemala: { name: '危地马拉', intro: '火山土壤与高海拔环境赋予危地马拉咖啡清晰酸质和可可甜感，安提瓜是最具代表性的精品产区之一。', note: '安提瓜、阿蒂特兰、薇薇特南果', color: '#5c7891' },
  Honduras: { name: '洪都拉斯', intro: '中美洲重要产地，产区海拔和微气候差异明显。常见红糖、核果、可可与柔和柑橘感，水洗样本尤其均衡。', note: '科潘、蒙特西略、阿加尔塔', color: '#7b8850' },
  'El Salvador': { name: '萨尔瓦多', intro: '以波旁品种和蜜处理见长。甜感集中、口感圆润，常有杏仁、红糖和成熟核果的组合。', note: '阿帕内卡、圣安娜、波旁', color: '#b56b49' },
  Nicaragua: { name: '尼加拉瓜', intro: '火山土壤与山地微气候形成柔和、甜感较高的杯型，日晒样本常表现出成熟水果、红糖与可可调性。', note: '希诺特加、新塞哥维亚、马塔加尔帕', color: '#4f7e70' },
  Mexico: { name: '墨西哥', intro: '墨西哥咖啡多来自南部高地，水洗样本常见坚果、可可和温和柑橘感，结构干净而甜感稳定。', note: '恰帕斯、瓦哈卡、韦拉克鲁斯', color: '#a0714d' },
  Peru: { name: '秘鲁', intro: '安第斯山地小农体系的重要产地。高海拔水洗豆常有红糖、柑橘和可可感，酸质清晰而不过分尖锐。', note: '卡哈马卡、库斯科、圣马丁', color: '#6e8061' },
  Bolivia: { name: '玻利维亚', intro: '安第斯高海拔产区的代表之一，核果、柑橘与红糖感常同时出现，兼具清晰度和柔和甜感。', note: '卡拉纳维、科帕卡巴纳、拉巴斯', color: '#9b6a52' },
  Ecuador: { name: '厄瓜多尔', intro: '洛哈等高海拔产区以细致花香、柑橘与核果感见长，浅烘时通常能保留轻盈茶感与干净余韵。', note: '洛哈、皮钦查、萨莫拉', color: '#64809b' },
  Tanzania: { name: '坦桑尼亚', intro: '东非高地咖啡常见莓果、柑橘和红茶感，酸质明亮并带有干净甜感，适合与肯尼亚样本比较。', note: '姆贝亚、乞力马扎罗、阿鲁沙', color: '#a95f54' },
  Uganda: { name: '乌干达', intro: '鲁文佐里山麓的阿拉比卡样本常有莓果、红糖与可可调性，果感饱满，口感相对厚实。', note: '鲁文佐里、布吉苏、西部高地', color: '#658151' },
  Burundi: { name: '布隆迪', intro: '高海拔小农样本常见红色莓果、柑橘和红茶感，酸质活泼、收尾清爽，是东非风味谱系的重要一环。', note: '卡扬扎、恩戈齐、基特加', color: '#9a5874' },
  India: { name: '印度', intro: '南印度高地阿拉比卡常有坚果、可可与温和香料感，质地圆润，适合观察中烘焙下的甜感与厚度。', note: '奇克马格鲁、马拉巴尔、尼尔吉里', color: '#9b7049' },
  Vietnam: { name: '越南', intro: '大叻高原代表越南精品阿拉比卡的发展方向，常见可可、红糖和熟果感，风格扎实而甜润。', note: '大叻、林同、山罗', color: '#6c7c59' },
  'Papua New Guinea': { name: '巴布亚新几内亚', intro: '山地小农体系下的咖啡兼具热带水果、柑橘和可可感，风味既有明亮度，也保留一定厚度。', note: '东部高地、西部高地、锡格里', color: '#6c7895' },
  Yemen: { name: '也门', intro: '传统高山日晒产地，常见酒香、干果和香料感，风味集中且具有鲜明的历史辨识度。', note: '哈拉兹、马塔里、萨那尼', color: '#936a4e' }
};

const mapMarkerOffsets = {
  'Costa Rica': [-15, 12], Panama: [14, 9], Guatemala: [-10, -10], Honduras: [9, -13],
  'El Salvador': [-13, -15], Nicaragua: [2, 13], Mexico: [-10, -8]
};

const fallbackLandForms = [
  { name: '北美洲', d: 'M72 151 C93 108, 145 83, 205 83 C252 84, 291 99, 321 126 C349 151, 353 184, 330 207 C306 231, 272 224, 250 247 C232 266, 203 270, 181 254 C154 233, 130 242, 111 219 C92 196, 62 188, 72 151Z M171 83 C154 57, 169 35, 202 32 C234 30, 262 45, 266 69 C236 69, 203 75, 171 83Z' },
  { name: '中美洲', d: 'M226 244 C249 238, 278 244, 301 257 C284 269, 260 275, 239 268 C226 264, 219 253, 226 244Z' },
  { name: '南美洲', d: 'M292 279 C331 271, 372 293, 386 334 C399 374, 381 406, 356 438 C337 462, 312 463, 306 431 C300 402, 276 383, 270 351 C263 314, 270 285, 292 279Z' },
  { name: '欧洲', d: 'M441 132 C469 105, 515 103, 548 123 C573 138, 570 163, 545 174 C515 187, 494 172, 468 182 C448 189, 424 178, 427 155 C428 146, 433 138, 441 132Z' },
  { name: '非洲', d: 'M466 196 C505 177, 551 190, 573 226 C599 268, 587 326, 553 363 C528 391, 493 384, 474 349 C455 315, 431 294, 438 254 C442 228, 449 205, 466 196Z' },
  { name: '中东', d: 'M564 190 C591 185, 614 197, 623 220 C613 240, 585 243, 568 229 C553 217, 548 200, 564 190Z' },
  { name: '亚洲', d: 'M552 121 C611 84, 701 88, 776 126 C832 154, 867 196, 842 231 C823 258, 773 249, 738 266 C696 286, 665 264, 626 260 C589 257, 565 236, 563 205 C561 177, 522 158, 552 121Z' },
  { name: '东南亚群岛', d: 'M681 277 C705 268, 727 276, 740 292 C724 304, 699 302, 681 292Z M746 300 C773 294, 803 304, 821 324 C795 337, 762 329, 746 300Z M686 329 C716 322, 745 333, 762 357 C732 367, 702 354, 686 329Z' },
  { name: '澳大利亚', d: 'M725 374 C771 346, 837 356, 867 399 C841 431, 783 434, 741 412 C721 401, 711 385, 725 374Z' }
];
mapLandForms.value = fallbackLandForms;

const categoryColors = {
  水果: '#d95f43', '花与草本': '#7a6aa6', '坚果可可': '#8a5138', 香料: '#b24f63', 甜感: '#b88727', 发酵: '#31745d'
};
const profiles = {
  bright: { title: '明亮果酸', label: '从柑橘、莓果与花香开始', text: '适合喜欢清晰酸质、轻盈口感与高海拔样本的探索者。', tags: ['citrus', 'berry', 'jasmine'], colors: ['#e9a07f', '#f1c96a'] },
  sweet: { title: '柔和甜感', label: '从红糖、核果与杏仁开始', text: '更圆润、更平衡，适合寻找甜感和柔和余韵的探索者。', tags: ['brownSugar', 'stone', 'almond'], colors: ['#e9c07b', '#b97c51'] },
  rich: { title: '醇厚可可', label: '从可可、坚果与香料开始', text: '厚度更高、尾韵更长，适合偏爱中深烘与浓郁质地的探索者。', tags: ['cocoa', 'almond', 'cinnamon'], colors: ['#a87354', '#d8a35c'] }
};
const guideSections = [
  { title: '豆子与基础概念', summary: '先把咖啡最常见的名词分清，再去看产区、处理法和风味会轻松很多。', cards: [
    ['单品豆', '来自单一产地、庄园或批次，重点是清楚表达地域、品种和处理法带来的风味个性。'], ['拼配豆', '把不同产地或烘焙曲线组合起来，通常追求稳定、平衡和固定风味轮廓。'], ['精品咖啡', '它强调风味、香气、口感、产地信息、生产方式与市场价值共同构成的独特性。'], ['Arabica', '精品咖啡中常见的物种，香气与酸甜层次通常更细，适合表达花香、果香和产地特征。'], ['Robusta', '咖啡因通常更高，口感厚重，苦感更明显，常用于意式拼配、速溶和奶咖。'], ['批次 / Lot', '同一产季或处理线路下的一组咖啡，是追溯质量和做样本比较时的基本单位。']
  ] },
  { title: '产地与品种', summary: '地理环境、品种遗传和产区管理，会直接影响一杯咖啡的骨架与风味方向。', cards: [
    ['产地', '不只是国家名，还包括地区、庄园、海拔、地块和处理站。信息越具体，风味追溯越完整。'], ['风土', '海拔、温度、降雨、土壤、遮荫和采收方式共同构成风土，影响成熟速度和风味潜力。'], ['海拔', '高海拔通常成熟更慢，酸质和香气结构往往更清晰，但仍要结合品种、气候和处理法。'], ['微气候', '同一庄园的坡向、遮荫和风向都可能改变成熟速度，让同产区样本出现差异。'], ['品种', '品种是咖啡遗传层面的差异，常见如 Typica、Bourbon、Caturra、SL28、Gesha。'], ['Gesha', '常以花香、柑橘、茶感和精致层次被认识，但表现仍取决于产地、熟度、处理与烘焙。']
  ] },
  { title: '处理法', summary: '咖啡果子变成咖啡豆之前，会经历去果肉、发酵和干燥，这一步对风味影响很大。', cards: [
    ['水洗', '去果肉后发酵、洗净并干燥，通常带来干净杯感、清楚酸质和稳定的产地表达。'], ['日晒', '整颗咖啡果直接干燥，常见甜感、莓果、酒香和发酵感更明显。'], ['蜜处理', '去果皮后保留部分黏液层干燥，介于水洗和日晒之间，甜感和干净度较平衡。'], ['厌氧发酵', '在低氧环境中控制发酵变量，更容易出现酒香、热带水果和明显的风味辨识度。'], ['湿刨', '常见于印尼，脱壳时豆体含水量较高，杯中常出现厚实、草本和低酸特征。'], ['干燥与含水率', '干燥速度、翻动频率和最终含水率会影响储存稳定性与杯测表现。']
  ] },
  { title: '冲煮与萃取', summary: '理解冲煮参数和萃取状态，能帮你判断一杯咖啡为什么这样喝起来。', cards: [
    ['手冲', '以热水分段注入粉层，控制水流、时间和扰动，适合表现香气、层次和产区细节。'], ['意式', '用高压在短时间内萃取高浓度咖啡液，风味集中，油脂和口感厚度明显。'], ['冷萃', '低温长时间浸泡，酸感和锐利感通常更低，口感更柔和顺滑。'], ['粉水比', '咖啡粉与水的比例是控制浓度和萃取结果的基础参数。'], ['研磨度与水温', '颗粒和温度共同影响流速与溶解速度，过细或过热都可能造成过萃。'], ['过萃与欠萃', '过萃常苦涩发干，欠萃常酸薄尖锐；应结合风味与参数一起调整。'], ['TDS 与萃取率', '它们能帮助量化浓度和可溶物比例，但不能替代完整的感官判断。'], ['通道效应', '水从局部阻力较小处快速穿透，会让同一杯同时出现欠萃和过萃。']
  ] },
  { title: '意式油脂与器具', summary: '认识 crema、磨豆机、滤杯和粉层工具，建立稳定的冲煮基础。', cards: [
    ['Crema 是什么', '意式表面的浅棕色泡沫层，来自油脂、二氧化碳、可溶物和微小颗粒共同形成。'], ['Crema 不等于品质', '油脂多不代表一定好喝，它只能提示豆子状态和萃取情况。'], ['磨豆机', '研磨均匀度直接影响萃取稳定性，很多时候比冲煮器具本身更重要。'], ['粉锤与布粉器', '目标是形成平整、稳定、阻力均匀的粉饼，减少结块和通道效应。'], ['滤杯与滤纸', '形状、肋骨和滤纸会改变流速、油脂、细粉与杯感干净度。'], ['电子秤', '用于控制粉量、注水量、出液量和时间，是复现配方的基础工具。']
  ] },
  { title: '烘焙与风味', summary: '烘焙决定产地特征如何被呈现，也会改变酸质、甜感、醇厚度与余韵。', cards: [
    ['浅烘', '更容易保留产地辨识度，常见花香、果香、茶感和清亮酸质。'], ['中烘', '酸甜与烘焙香更平衡，常见坚果、焦糖、巧克力和柔和果酸。'], ['深烘', '烘焙感更强，苦甜更突出，常带可可、焦糖、烟熏或木质调性。'], ['梅纳反应', '糖和氨基酸加热产生褐变与香气前体，是烘焙风味形成的重要路径。'], ['一爆与发展时间', '一爆后的阶段决定香气展开；过短尖锐生青，过长会压掉产地细节。'], ['酸质、Body、余韵', '酸质是活力，Body 是口腔重量，余韵是吞咽后香气与味道的延续。'], ['平衡与干净度', '好的咖啡不是单项最强，而是酸甜苦、香气、质感和尾韵彼此协调。']
  ] },
  { title: '感官描述', summary: '风味词要可沟通、可复现，并且能和样本数据对应。', cards: [
    ['干香与湿香', '干香来自研磨后的粉，湿香来自注水后的粉层；两者能提示不同阶段的香气变化。'], ['风味轮', '从中心大类向外层具体词汇逐步定位，帮助不同人使用更一致的语言。'], ['花香', '可能接近茉莉、橙花、玫瑰或蜂蜜花香，常见于部分高海拔样本。'], ['果香', '可进一步描述为柑橘、莓果、核果、热带水果或干果，尽量避免只说“水果味”。'], ['坚果与可可', '常见于中烘样本，可能表现为杏仁、榛果、可可粉或黑巧克力。'], ['发酵与酒香', '来自处理过程中的代谢产物，关键是干净、可控且与甜感和酸质协调。']
  ] }
];

const navItems = [
  { id: 'discover', label: '按口味找豆' },
  { id: 'map', label: '产地地图' }, { id: 'beans', label: '豆库' }, { id: 'flavors', label: '风味分析' },
  { id: 'guide', label: '咖啡秘籍' }
];
const guideSectionIndex = ref(0);

const activeProfile = computed(() => profiles[discovery.value]);
const isAdmin = computed(() => currentUser.value?.role === 'admin' || currentUser.value?.isAdmin);
const countries = computed(() => [...new Set(coffees.value.map(c => c.country).filter(Boolean))]);
const processes = computed(() => [...new Set(coffees.value.map(c => c.process).filter(Boolean))]);
const roastLevels = computed(() => [...new Set(coffees.value.map(c => c.roast).filter(Boolean))]);
const profileCounts = computed(() => Object.fromEntries(
  Object.entries(profiles).map(([key, profile]) => [
    key,
    coffees.value.filter(coffee => profile.tags.some(tag => Number(coffee.flavors?.[tag] || 0) > 0)).length
  ])
));
const rankedDiscovery = computed(() => rankBeans(coffees.value, activeProfile.value.tags, {
  process: discoveryProcess.value, roast: discoveryRoast.value
}));
const discoveryPicks = computed(() => rankedDiscovery.value.slice(0, 3));
const flavorMap = computed(() => Object.fromEntries(tags.value.map(t => [t.id, t])));
const categoryMap = computed(() => Object.fromEntries(categories.value.map(c => [c.name, c])));

const filteredCoffees = computed(() => coffees.value.filter(coffee => {
  const q = searchQuery.value.trim().toLowerCase();
  const flavorText = Object.keys(coffee.flavors || {}).map(id => flavorMap.value[id]?.name || id).join(' ');
  const text = [coffee.name, coffee.country, countryLabel(coffee.country), coffee.region, coffee.variety, coffee.process, flavorText].join(' ').toLowerCase();
  return (!q || text.includes(q)) && (countryFilter.value === 'all' || coffee.country === countryFilter.value) &&
    (processFilter.value === 'all' || coffee.process === processFilter.value) &&
    (!selectedFlavor.value || Number(coffee.flavors?.[selectedFlavor.value] || 0) > 0);
}));

const beanResults = computed(() => coffees.value.filter(coffee => {
  const q = beanSearch.value.trim().toLowerCase();
  return (!q || [coffee.name, coffee.region, countryLabel(coffee.country)].join(' ').toLowerCase().includes(q)) &&
    (beanCountry.value === 'all' || coffee.country === beanCountry.value) && (beanProcess.value === 'all' || coffee.process === beanProcess.value);
}));
const selectedCoffee = computed(() => coffees.value.find(c => c.id === selectedCoffeeId.value) || filteredCoffees.value[0] || coffees.value[0]);
const compareCoffees = computed(() => compareIds.value.map(id => coffees.value.find(c => c.id === id)).filter(Boolean));
const comparisonFocusCoffee = computed(() => compareCoffees.value.find(c => c.id === comparisonFocusId.value));
const mapOrigins = computed(() => countries.value.map(country => {
  mapProjectionVersion.value;
  const samples = coffees.value.filter(coffee => coffee.country === country);
  const longitude = samples.reduce((sum, coffee) => sum + Number(coffee.longitude || 0), 0) / Math.max(samples.length, 1);
  const latitude = samples.reduce((sum, coffee) => sum + Number(coffee.latitude || 0), 0) / Math.max(samples.length, 1);
  const regions = [...new Set(samples.map(coffee => coffee.region).filter(Boolean))];
  const flavorTotals = new Map();
  samples.forEach(coffee => Object.entries(coffee.flavors || {}).forEach(([id, value]) => flavorTotals.set(id, (flavorTotals.get(id) || 0) + Number(value || 0))));
  const flavors = [...flavorTotals.entries()].sort((a, b) => b[1] - a[1]).slice(0, 4).map(([id]) => tagName(id));
  const meta = countryMeta[country] || {};
  return {
    country, samples, sampleCount: samples.length, longitude, latitude,
    x: projectMap({ longitude, latitude }).x, y: projectMap({ longitude, latitude }).y,
    region: regions.slice(0, 3).join('、') || meta.note || '产区资料待补充',
    flavors, description: meta.intro || samples[0]?.description || '来自数据库样本的产地记录。',
    ...meta
  };
}));
const activeOrigin = computed(() => mapOrigins.value.find(origin => origin.country === mapCountry.value));
const ratio = computed(() => brew.value.dose ? (brew.value.water / brew.value.dose).toFixed(1) : '0.0');
const brewAdvice = computed(() => {
  if (!selectedCoffee.value) return '选择样本后，这里会根据处理法和烘焙度给出参数提示。';
  const roast = selectedCoffee.value.roast || '';
  const process = selectedCoffee.value.process || '';
  if (roast.includes('深')) return '当前样本偏深烘，建议降低水温并缩短接触时间，先从 90°C / 1:15 开始。';
  if (process.includes('日晒') || process.includes('厌氧')) return '当前样本风味表达较强，建议保持 91–92°C，减少搅拌，优先观察甜感和余韵。';
  return '当前样本适合从 92°C、1:16 粉水比开始，再根据酸质和余韵微调。';
});
const extractionYield = computed(() => {
  const dose = Number(extraction.value.dose);
  const beverage = Number(extraction.value.beverage);
  const tds = Number(extraction.value.tds);
  return dose > 0 ? (beverage * tds / dose).toFixed(1) : '0.0';
});
const extractionStatus = computed(() => {
  const value = Number(extractionYield.value);
  if (!Number.isFinite(value) || value <= 0) return { label: '等待数据', tone: 'neutral', hint: '输入饮品重量和 TDS 后估算。' };
  if (value < 18) return { label: '可能欠萃', tone: 'low', hint: '尝试更细研磨、提高水温或延长接触时间。' };
  if (value > 22) return { label: '可能过萃', tone: 'high', hint: '尝试更粗研磨、降低水温或缩短接触时间。' };
  return { label: '常见平衡区间', tone: 'good', hint: '再结合酸、甜、苦和余韵进行感官确认。' };
});
const timerDisplay = computed(() => {
  const minutes = Math.floor(brewTimerElapsed.value / 60).toString().padStart(2, '0');
  const seconds = (brewTimerElapsed.value % 60).toString().padStart(2, '0');
  return `${minutes}:${seconds}`;
});
const timerProgress = computed(() => Math.min(100, brewTimerElapsed.value / Math.max(Number(brew.value.time) || 1, 1) * 100));
const converterResult = computed(() => {
  const value = Number(converter.value.value) || 0;
  if (converter.value.type === 'temperature') return `${value.toFixed(1)} °C  =  ${(value * 9 / 5 + 32).toFixed(1)} °F`;
  if (converter.value.type === 'volume') return `${value.toFixed(1)} ml  =  ${(value * 0.033814).toFixed(1)} fl oz`;
  return `${value.toFixed(1)} g  =  ${(value * 0.035274).toFixed(2)} oz`;
});
const cuppingTotal = computed(() => Object.values(cuppingForm.value).slice(0, 5).reduce((sum, value) => sum + Number(value || 0), 0));
const cuppingAverage = computed(() => (cuppingTotal.value / 5).toFixed(1));

const wheelSegments = computed(() => {
  const source = tags.value.length ? tags.value : [
    { id: 'citrus', name: '柑橘', category: '水果' }, { id: 'berry', name: '莓果', category: '水果' },
    { id: 'stone', name: '核果', category: '水果' }, { id: 'jasmine', name: '茉莉', category: '花与草本' },
    { id: 'herbal', name: '草本', category: '花与草本' }, { id: 'cocoa', name: '可可', category: '坚果可可' },
    { id: 'almond', name: '杏仁', category: '坚果可可' }, { id: 'cinnamon', name: '肉桂', category: '香料' },
    { id: 'brownSugar', name: '红糖', category: '甜感' }, { id: 'wine', name: '酒香', category: '发酵' }
  ];
  const grouped = source.reduce((all, tag) => { (all[tag.category] ||= []).push(tag); return all; }, {});
  const entries = [];
  let cursor = -Math.PI / 2;
  Object.entries(grouped).forEach(([category, items]) => {
    const span = (Math.PI * 2 * items.length) / source.length;
    items.forEach((tag, index) => {
      const start = cursor + (span * index / items.length) + 0.014;
      const end = cursor + (span * (index + 1) / items.length) - 0.014;
      entries.push({ ...tag, start, end, mid: (start + end) / 2, color: categoryColors[category] || '#6e8775' });
    });
    cursor += span;
  });
  return entries;
});

function countryLabel(country) { return countryNames[country] || country || '未知产地'; }
function tagName(id) { return flavorMap.value[id]?.name || id; }
function tagCategory(id) { return flavorMap.value[id]?.category || '其他'; }
function topFlavors(coffee, limit = 3) { return Object.entries(coffee.flavors || {}).sort((a, b) => b[1] - a[1]).slice(0, limit); }
function pct(value) { return `${Math.max(0, Math.min(100, Number(value || 0) * 20))}%`; }
function polar(radius, angle, cx = 260, cy = 260) { return { x: cx + Math.cos(angle) * radius, y: cy + Math.sin(angle) * radius }; }
function arcPath(inner, outer, start, end) {
  const a = polar(outer, start), b = polar(outer, end), c = polar(inner, end), d = polar(inner, start);
  const large = end - start > Math.PI ? 1 : 0;
  return `M ${a.x} ${a.y} A ${outer} ${outer} 0 ${large} 1 ${b.x} ${b.y} L ${c.x} ${c.y} A ${inner} ${inner} 0 ${large} 0 ${d.x} ${d.y} Z`;
}
function labelPoint(segment) { return polar(143, segment.mid); }
function projectMap(coffee) {
  if (worldProjection) {
    const [x, y] = worldProjection([Number(coffee.longitude || 0), Number(coffee.latitude || 0)]);
    return { x, y };
  }
  return { x: 80 + ((Number(coffee.longitude || 0) + 180) / 360) * 760, y: 60 + ((90 - Number(coffee.latitude || 0)) / 180) * 300 };
}
function mapLabelWidth(country) { return Math.max(54, countryLabel(country).length * 12 + 22); }
function mapProfile(country) { return countryMeta[country] || { color: '#2f6f59' }; }
function mapFocusTarget(origin) {
  if (!origin) return [0, 0, 920, 500];
  const zoom = 1.72;
  const viewW = 920 / zoom;
  const viewH = 500 / zoom;
  const x = Math.max(-18, Math.min(origin.x - viewW / 2, 920 - viewW + 18));
  const y = Math.max(-16, Math.min(origin.y - viewH / 2, 500 - viewH + 16));
  return [x, y, viewW, viewH];
}
function setMapViewBox(box) { mapViewBox.value = box.map(value => Number(value.toFixed(2))).join(' '); }
function animateMapViewBox(target) {
  if (mapAnimationFrame) cancelAnimationFrame(mapAnimationFrame);
  const current = mapViewBox.value.split(' ').map(Number);
  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (reduceMotion || current.every((value, index) => Math.abs(value - target[index]) < 0.1)) { setMapViewBox(target); return; }
  const startedAt = performance.now();
  const duration = 680;
  const ease = value => 1 - Math.pow(1 - value, 3);
  const step = now => {
    const progress = Math.min(1, (now - startedAt) / duration);
    const eased = ease(progress);
    setMapViewBox(current.map((value, index) => value + (target[index] - value) * eased));
    if (progress < 1) mapAnimationFrame = requestAnimationFrame(step);
    else mapAnimationFrame = null;
  };
  mapAnimationFrame = requestAnimationFrame(step);
}
function focusMapCountry(country) {
  mapCountry.value = country;
  const origin = mapOrigins.value.find(item => item.country === country);
  if (origin?.samples[0]) selectedCoffeeId.value = origin.samples[0].id;
}
function clearMapFocus() { mapHoverCountry.value = ''; mapCountry.value = ''; }

async function loadWorldMap() {
  if (!window.d3 || !window.topojson) return;
  try {
    const response = await fetch('https://unpkg.com/world-atlas@2/countries-110m.json');
    if (!response.ok) return;
    const topology = await response.json();
    const world = window.topojson.feature(topology, topology.objects.countries);
    worldProjection = window.d3.geoNaturalEarth1().fitSize([920, 500], world);
    mapLandForms.value = world.features.map((feature, index) => ({ name: `country-${feature.id || index}`, d: window.d3.geoPath(worldProjection)(feature) }));
    mapProjectionVersion.value += 1;
  } catch { /* Keep the bundled fallback map when the topology cannot load. */ }
}

async function api(url, options = {}) {
  const response = await fetch(url, { headers: { 'Content-Type': 'application/json', ...(options.headers || {}) }, ...options });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(payload.error || `请求失败 (${response.status})`);
  return payload;
}
async function load() {
  loading.value = true;
  try {
    let data;
    let session;
    try {
      [data, session] = await Promise.all([api('/api/bootstrap'), api('/api/session')]);
    } catch {
      const staticData = await fetch(`${import.meta.env.BASE_URL}bootstrap.json`).then(response => response.json());
      data = staticData;
      session = { authenticated: false, user: null };
    }
    categories.value = data.categories || [];
    tags.value = data.tags || [];
    coffees.value = data.coffees || [];
    currentUser.value = session.authenticated ? session.user : null;
    selectedCoffeeId.value = coffees.value[0]?.id || null;
    errorMessage.value = '';
  } catch (error) { errorMessage.value = error.message; }
  finally { loading.value = false; }
}
function go(target) {
  const allowed = ['home', 'discover', 'map', 'beans', 'flavors', 'guide', 'tools', 'tasting', 'samples', 'tags', 'account', 'login'];
  if (['samples', 'tags'].includes(target) && !isAdmin.value) target = currentUser.value ? 'account' : 'login';
  view.value = allowed.includes(target) ? target : 'home';
  mobileNavOpen.value = false;
  window.location.hash = view.value;
  window.scrollTo({ top: 0, behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth' });
}
function setFlavor(id) {
  selectedFlavor.value = selectedFlavor.value === id ? '' : id;
  const match = filteredCoffees.value[0] || coffees.value.find(c => c.flavors?.[selectedFlavor.value]);
  if (match) selectedCoffeeId.value = match.id;
  if (selectedFlavor.value && !compareIds.value.length) compareMatchingSamples();
}
function compareMatchingSamples() {
  compareIds.value = [...filteredCoffees.value]
    .sort((a, b) => Number(b.flavors?.[selectedFlavor.value] || 0) - Number(a.flavors?.[selectedFlavor.value] || 0))
    .slice(0, 3).map(coffee => coffee.id);
  comparisonFocusId.value = null;
}
function startDiscovery(key) {
  discovery.value = key;
  discoveryProcess.value = 'all'; discoveryRoast.value = 'all';
  go('discover');
}
function saveSampleImage(data) {
  const coffee = coffees.value.find(item => item.id === data.id);
  if (coffee) coffee.imageUrl = data.imageUrl;
}
function resetFlavor() { selectedFlavor.value = ''; }
function scrollToFinder() { document.getElementById('taste-finder')?.scrollIntoView({ behavior: 'smooth' }); }
function toggleCompare(coffee) {
  if (compareIds.value.includes(coffee.id)) compareIds.value = compareIds.value.filter(id => id !== coffee.id);
  else if (compareIds.value.length < 4) compareIds.value = [...compareIds.value, coffee.id];
}
async function discover() {
  const picks = discoveryPicks.value.map(item => item.coffee);
  if (!picks.length) return;
  compareIds.value = picks.map(c => c.id);
  selectedCoffeeId.value = picks[0].id;
  selectedFlavor.value = '';
  searchQuery.value = '';
  countryFilter.value = 'all';
  processFilter.value = 'all';
  go('flavors');
  await scrollToComparison();
}
async function scrollToComparison() {
  await nextTick();
  document.getElementById('comparison-title')?.scrollIntoView({ block: 'start', behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth' });
}
async function compareBean(coffee) {
  if (!compareIds.value.includes(coffee.id) && compareIds.value.length >= 4) return;
  selectedCoffeeId.value = coffee.id;
  if (!compareIds.value.includes(coffee.id) && compareIds.value.length < 4) compareIds.value = [...compareIds.value, coffee.id];
  closeModal();
  go('flavors');
  await scrollToComparison();
}
function visitBeanOrigin(coffee) {
  mapCountry.value = coffee.country;
  closeModal();
  go('map');
}
async function openBean(coffee) { modalCoffee.value = coffee; reviewError.value = ''; reviewForm.value = { rating: 5, content: '' }; await loadReviews(coffee.id); }
function closeModal() { modalCoffee.value = null; reviews.value = []; }
async function loadReviews(sampleId) {
  try {
    const payload = await api(`/api/reviews/${sampleId}`);
    reviews.value = payload.reviews || [];
    reviewSummary.value = { count: payload.count || 0, average: payload.average || 0 };
  }
  catch (error) { reviewError.value = error.message; }
}
async function submitReview() {
  if (!modalCoffee.value) return;
  if (!currentUser.value) { closeModal(); go('login'); return; }
  reviewBusy.value = true; reviewError.value = '';
  try { await api(`/api/reviews/${modalCoffee.value.id}`, { method: 'POST', body: JSON.stringify(reviewForm.value) }); reviewForm.value = { rating: 5, content: '' }; await loadReviews(modalCoffee.value.id); }
  catch (error) { reviewError.value = error.message; }
  finally { reviewBusy.value = false; }
}
async function submitAuth() {
  authBusy.value = true; authError.value = '';
  try {
    const endpoint = authMode.value === 'register' ? '/api/register' : '/api/login';
    const payload = await api(endpoint, { method: 'POST', body: JSON.stringify(loginForm.value) });
    currentUser.value = payload.user; loginForm.value = { username: '', password: '' }; go('account');
  } catch (error) { authError.value = error.message; }
  finally { authBusy.value = false; }
}
async function logout() {
  await api('/api/logout', { method: 'POST' }); currentUser.value = null; go('home');
}
async function createAdminSample() {
  adminBusy.value = true; adminError.value = '';
  try {
    const form = adminSampleForm.value;
    const flavors = Object.fromEntries(tags.value.slice(0, 4).map((tag, index) => [tag.id, Math.max(2, 5 - index)]));
    const created = await api('/api/samples', { method: 'POST', body: JSON.stringify({ ...form, latitude: Number(form.latitude || 0), longitude: Number(form.longitude || 0), flavors }) });
    adminSampleForm.value = { name: '', country: 'China', region: '', species: 'Arabica', variety: '', process: '水洗', roast: '中浅烘', altitude: '', year: '2025', latitude: '', longitude: '', description: '' };
    await load();
    adminImageSampleId.value = created.id;
  } catch (error) { adminError.value = error.message; }
  finally { adminBusy.value = false; }
}
async function createAdminTag() {
  adminBusy.value = true; adminError.value = '';
  try { await api('/api/tags', { method: 'POST', body: JSON.stringify(adminTagForm.value) }); adminTagForm.value = { name: '', category: '', description: '' }; await load(); }
  catch (error) { adminError.value = error.message; }
  finally { adminBusy.value = false; }
}
async function deleteAdminSample(id) {
  if (!window.confirm('确认删除这个样本吗？')) return;
  try { await api(`/api/samples/${id}`, { method: 'DELETE' }); await load(); } catch (error) { adminError.value = error.message; }
}
async function deleteAdminTag(id) {
  if (!window.confirm('确认删除这个风味标签吗？')) return;
  try { await api(`/api/tags/${encodeURIComponent(id)}`, { method: 'DELETE' }); await load(); } catch (error) { adminError.value = error.message; }
}
function toggleBrewTimer() {
  brewTimerRunning.value = !brewTimerRunning.value;
  if (brewTimerRunning.value) {
    brewTimerInterval = window.setInterval(() => {
      brewTimerElapsed.value += 1;
      if (brewTimerElapsed.value >= Number(brew.value.time || 0)) {
        brewTimerRunning.value = false;
        window.clearInterval(brewTimerInterval);
        brewTimerInterval = null;
      }
    }, 1000);
  } else {
    window.clearInterval(brewTimerInterval);
    brewTimerInterval = null;
  }
}
function resetBrewTimer() {
  brewTimerRunning.value = false;
  brewTimerElapsed.value = 0;
  window.clearInterval(brewTimerInterval);
  brewTimerInterval = null;
}
function saveCuppingNote() {
  const key = `coffee-atlas-cupping-${selectedCoffee.value?.id || 'scratch'}`;
  localStorage.setItem(key, JSON.stringify({ ...cuppingForm.value, savedAt: new Date().toISOString() }));
  cuppingSaved.value = true;
  window.setTimeout(() => { cuppingSaved.value = false; }, 2200);
}
function loadCuppingNote() {
  const key = `coffee-atlas-cupping-${selectedCoffee.value?.id || 'scratch'}`;
  const saved = localStorage.getItem(key);
  if (!saved) return;
  try { cuppingForm.value = { ...cuppingForm.value, ...JSON.parse(saved) }; } catch { /* Ignore malformed local notes. */ }
}
watch(selectedCoffeeId, loadCuppingNote);

watch(view, value => { document.title = `${({ home: '咖啡风味图谱', discover: '按口味找豆', map: '产地地图', beans: '咖啡豆库', flavors: '风味分析', guide: '咖啡秘籍', tools: '咖啡工具', account: '个人账户', login: '登录账户' })[value] || 'Coffee Flavor Atlas'} | Coffee Flavor Atlas`; });
watch(mapCountry, async value => {
  await nextTick();
  animateMapViewBox(mapFocusTarget(mapOrigins.value.find(origin => origin.country === value)));
});
watch(mapProjectionVersion, async () => {
  if (!mapCountry.value) return;
  await nextTick();
  animateMapViewBox(mapFocusTarget(mapOrigins.value.find(origin => origin.country === mapCountry.value)));
});
onMounted(() => { window.addEventListener('hashchange', () => { view.value = window.location.hash.slice(1) || 'home'; }); load(); loadWorldMap(); });
onBeforeUnmount(() => {
  if (mapAnimationFrame) cancelAnimationFrame(mapAnimationFrame);
  if (brewTimerInterval) window.clearInterval(brewTimerInterval);
});
</script>

<template>
  <div class="app" :class="`view-${view}`">
    <header class="site-header">
      <a class="brand" href="#home" @click.prevent="go('home')" aria-label="回到首页">
        <span class="brand-mark"><i></i><i></i><i></i></span><span>COFFEE<br /><b>ATLAS</b></span>
      </a>
      <button class="mobile-menu" type="button" @click="mobileNavOpen = !mobileNavOpen" aria-label="打开导航"><span></span><span></span></button>
      <nav class="nav" :class="{ open: mobileNavOpen }" aria-label="主导航">
        <button v-for="item in navItems" :key="item.id" type="button" :class="{ active: view === item.id }" @click="go(item.id)">{{ item.label }}</button>
        <span class="nav-rule"></span>
        <button type="button" :class="{ active: ['tools', 'tasting'].includes(view) }" @click="go('tools')">工具</button>
        <button type="button" class="account-link" :class="{ active: ['login', 'account'].includes(view) }" @click="go(currentUser ? 'account' : 'login')"><span class="account-dot"></span>{{ currentUser ? currentUser.username : '账户' }}</button>
      </nav>
    </header>

    <main>
      <div v-if="errorMessage" class="status error"><strong>本地服务未连接</strong><span>{{ errorMessage }}</span><button @click="load">重新连接</button></div>
      <div v-else-if="loading" class="loading-state"><span class="skeleton wide"></span><span class="skeleton"></span><span class="skeleton"></span></div>

      <template v-else>
        <AtlasHome v-if="view === 'home'" :profiles="profiles" :profile-counts="profileCounts" :sample-count="coffees.length" :country-count="countries.length" @start="startDiscovery" @navigate="go" />
        <section v-else-if="view === 'discover'" class="home-page page-enter">
          <div class="home-hero">
            <div class="hero-copy">
              <p class="kicker">COFFEE ATLAS / FIND YOUR CUP</p>
              <h1>找到你喜欢的<br /><em>下一款咖啡。</em></h1>
              <p class="hero-lede">从熟悉的风味出发，在真实样本中找相近的豆子。看清风味、处理法与烘焙度，再决定下一杯喝什么。</p>
              <button class="primary-button" @click="scrollToFinder">按口味找豆 <span>↓</span></button>
            </div>
            <div class="hero-visual home-feature" :style="{ '--profile-color': activeProfile.colors[0] }">
              <p class="kicker">当前口味 · {{ activeProfile.title }}</p>
              <template v-if="discoveryPicks.length">
                <div class="home-feature-main"><span>01 / {{ String(discoveryPicks.length).padStart(2, '0') }}</span><h2>{{ discoveryPicks[0].coffee.name }}</h2><p>{{ countryLabel(discoveryPicks[0].coffee.country) }} · {{ discoveryPicks[0].coffee.region }} · {{ discoveryPicks[0].coffee.process }}</p></div>
                <div class="home-feature-flavors"><span v-for="match in discoveryPicks[0].matches" :key="match.id">{{ tagName(match.id) }} <b>{{ match.intensity }} / 5</b></span></div>
                <button class="line-button" @click="openBean(discoveryPicks[0].coffee)">查看这款豆子 <span>↗</span></button>
              </template>
              <p v-else class="home-feature-empty">当前条件没有对应样本</p>
            </div>
          </div>
          <div id="taste-finder" class="home-divider"><span>01 / 选择你喜欢的口味</span><span>{{ coffees.length }} 款数据库样本</span></div>
          <div class="taste-paths">
            <button v-for="(profile, key, index) in profiles" :key="key" class="taste-path" :class="{ selected: discovery === key }" :aria-pressed="discovery === key" @click="discovery = key">
              <span class="path-index">0{{ index + 1 }}</span><span class="path-orb" :style="{ background: profile.colors[0] }"></span><span><b>{{ profile.title }}</b><small>{{ profile.label }}</small></span><span class="path-arrow" aria-hidden="true">→</span>
            </button>
          </div>
          <div class="finder-controls">
            <div><p class="kicker">02 / 缩小范围</p><p>{{ activeProfile.text }}</p></div>
            <div class="finder-fields"><label>处理法<select v-model="discoveryProcess"><option value="all">不限处理法</option><option v-for="process in processes" :key="process" :value="process">{{ process }}</option></select></label><label>烘焙度<select v-model="discoveryRoast"><option value="all">不限烘焙度</option><option v-for="roast in roastLevels" :key="roast" :value="roast">{{ roast }}</option></select></label></div>
          </div>
          <section class="finder-results" aria-live="polite">
            <div class="finder-heading"><div><p class="kicker">03 / 与口味相近的样本</p><h2>{{ activeProfile.title }} <small>{{ rankedDiscovery.length }} 款有风味交集</small></h2></div><span>按命中风味数量、强度排序</span></div>
            <div v-if="discoveryPicks.length" class="finder-grid">
              <article v-for="(result, index) in discoveryPicks" :key="result.coffee.id" class="finder-card" :style="{ '--profile-color': activeProfile.colors[0] }">
                <div class="finder-card-top"><span>0{{ index + 1 }} / {{ countryLabel(result.coffee.country) }}</span><strong>命中 {{ result.coverage }}/{{ activeProfile.tags.length }} 种</strong></div>
                <h3>{{ result.coffee.name }}</h3><p class="finder-origin">{{ result.coffee.region }} · {{ result.coffee.process }} · {{ result.coffee.roast }}</p>
                <div class="finder-reasons"><span v-for="match in result.matches" :key="match.id">{{ tagName(match.id) }} <b>{{ match.intensity }}/5</b></span></div>
                <button class="line-button" @click="openBean(result.coffee)">查看豆子与评价 <span>↗</span></button>
              </article>
            </div>
            <div v-else class="finder-empty"><p>当前条件下没有风味相近的样本。</p><button class="text-button" @click="discoveryProcess = 'all'; discoveryRoast = 'all'">清除筛选</button></div>
            <div class="finder-actions"><button class="primary-button" :disabled="!discoveryPicks.length" @click="discover">对比这 {{ discoveryPicks.length }} 款 <span>→</span></button><button class="line-button" @click="go('beans')">浏览全部豆库 <span>↗</span></button></div>
          </section>
        </section>

        <section v-else-if="view === 'map'" class="page-shell page-enter">
          <div class="section-heading"><div><p class="kicker">01 / ORIGIN INDEX</p><h1>产地地图</h1><p>把咖啡样本放回它真实的山地、气候与文化脉络。</p></div><div class="heading-stat"><strong>{{ mapOrigins.length }}</strong><span>个经典产国</span></div></div>
          <div class="map-layout">
            <div class="world-map panel-line">
              <svg ref="mapSvg" class="world-map-svg" viewBox="0 0 920 500" :viewBox="mapViewBox" role="img" aria-label="全球咖啡产地地图" @click="clearMapFocus">
                <defs>
                  <pattern id="map-grid-pattern" width="92" height="50" patternUnits="userSpaceOnUse">
                    <path d="M 92 0 L 0 0 0 50" fill="none" stroke="#7b9a8b" stroke-opacity=".18" />
                  </pattern>
                </defs>
                <rect width="920" height="500" fill="url(#map-grid-pattern)" />
                <g class="world-land">
                  <path v-for="(land, index) in mapLandForms" :key="land.name" :d="land.d" :class="`land-shape land-${index}`" />
                </g>
                <g v-if="activeOrigin" class="map-focus-ring" pointer-events="none">
                  <circle :cx="activeOrigin.x + (mapMarkerOffsets[activeOrigin.country]?.[0] || 0)" :cy="activeOrigin.y + (mapMarkerOffsets[activeOrigin.country]?.[1] || 0)" r="25" />
                  <circle class="map-focus-pulse" :cx="activeOrigin.x + (mapMarkerOffsets[activeOrigin.country]?.[0] || 0)" :cy="activeOrigin.y + (mapMarkerOffsets[activeOrigin.country]?.[1] || 0)" r="25" />
                </g>
                <g v-for="origin in mapOrigins" :key="origin.country" class="map-country-node" :class="{ selected: mapCountry === origin.country }" role="button" tabindex="0" :aria-label="`${countryLabel(origin.country)}，点击查看产地介绍`" @click.stop="focusMapCountry(origin.country)" @mouseenter="mapHoverCountry = origin.country" @mouseleave="mapHoverCountry = ''" @keydown.enter.stop="focusMapCountry(origin.country)" @keydown.space.prevent.stop="focusMapCountry(origin.country)">
                  <line v-if="mapMarkerOffsets[origin.country]" class="map-marker-leader" :x1="origin.x" :y1="origin.y" :x2="origin.x + mapMarkerOffsets[origin.country][0]" :y2="origin.y + mapMarkerOffsets[origin.country][1]" :stroke="mapProfile(origin.country).color" />
                  <circle class="map-point-hit" :cx="origin.x + (mapMarkerOffsets[origin.country]?.[0] || 0)" :cy="origin.y + (mapMarkerOffsets[origin.country]?.[1] || 0)" r="18" />
                  <circle class="map-point" :cx="origin.x + (mapMarkerOffsets[origin.country]?.[0] || 0)" :cy="origin.y + (mapMarkerOffsets[origin.country]?.[1] || 0)" :r="mapCountry === origin.country ? 9 : 6.5" :fill="mapCountry === origin.country ? mapProfile(origin.country).color : '#2f6f59'" />
                  <g v-if="mapHoverCountry === origin.country || mapCountry === origin.country" class="map-label" :transform="`translate(${origin.x + (mapMarkerOffsets[origin.country]?.[0] || 0)}, ${origin.y + (mapMarkerOffsets[origin.country]?.[1] || 0) - 24})`">
                    <rect :x="-mapLabelWidth(origin.country) / 2" y="-17" :width="mapLabelWidth(origin.country)" height="25" rx="4" />
                    <text y="0" text-anchor="middle">{{ countryLabel(origin.country) }}</text>
                  </g>
                </g>
              </svg>
              <div class="map-scale">180°W <span></span> 0° <span></span> 180°E</div>
            </div>
            <aside class="origin-panel panel-line" :class="{ filled: mapCountry }">
              <template v-if="activeOrigin"><button class="close-text" @click="clearMapFocus">清除聚焦 ×</button><p class="kicker">ORIGIN PROFILE</p><div class="origin-card-accent" :style="{ background: activeOrigin.color || '#2f6f59' }"></div><h2>{{ countryLabel(activeOrigin.country) }}</h2><p class="origin-description">{{ activeOrigin.description }}</p><div class="origin-meta"><span>代表区域</span><b>{{ activeOrigin.region }}</b><span>样本数量</span><b>{{ activeOrigin.sampleCount }} 款</b></div><div class="origin-flavor-list"><span class="kicker">常见风味方向</span><div class="origin-chip-row"><span v-for="flavor in activeOrigin.flavors" :key="flavor" class="origin-chip">{{ flavor }}</span><span v-if="!activeOrigin.flavors.length" class="origin-chip">持续补充中</span></div></div><button class="line-button" @click="beanCountry = activeOrigin.country; go('beans')">查看该产国样本 →</button></template>
              <template v-else><p class="kicker">ORIGIN PROFILE</p><h2>选择一个产国</h2><p>悬浮查看名称，点击标记聚焦地图，并查看该产国的代表区域与样本。</p><div class="origin-list"><button v-for="origin in mapOrigins.slice(0, 7)" :key="origin.country" @click="focusMapCountry(origin.country)"><span></span>{{ countryLabel(origin.country) }}<b>{{ origin.sampleCount }}</b></button></div></template>
            </aside>
          </div>
        </section>

        <section v-else-if="view === 'beans'" class="page-shell page-enter">
          <div class="section-heading"><div><p class="kicker">02 / SAMPLE LIBRARY</p><h1>咖啡豆库</h1><p>用同一套字段阅读不同产地的样本表达。</p></div><div class="heading-stat"><strong>{{ beanResults.length }}</strong><span>当前样本</span></div></div>
          <div class="filter-bar"><label><span>搜索样本</span><input v-model="beanSearch" placeholder="名称、产区或国家" /></label><label><span>产国</span><select v-model="beanCountry"><option value="all">全部产国</option><option v-for="country in countries" :key="country" :value="country">{{ countryLabel(country) }}</option></select></label><label><span>处理法</span><select v-model="beanProcess"><option value="all">全部处理法</option><option v-for="process in processes" :key="process">{{ process }}</option></select></label></div>
          <div class="bean-grid">
            <article v-for="(coffee, index) in beanResults" :key="coffee.id" class="bean-card bean-card-photo" :style="{ '--i': Math.min(index, 8) }" role="button" tabindex="0" :aria-label="`查看${coffee.name}详情`" @click="openBean(coffee)" @keydown.enter="openBean(coffee)" @keydown.space.prevent="openBean(coffee)">
              <BeanImage :coffee="coffee" />
              <div class="bean-card-top"><span class="bean-country">{{ countryLabel(coffee.country) }}</span><span class="bean-number">{{ coffee.roast }}</span></div>
              <div class="bean-card-copy"><h2>{{ coffee.name }}</h2><p>{{ coffee.region }} · {{ coffee.process }}</p><div class="tag-row"><span v-for="([id, value]) in topFlavors(coffee)" :key="id" :style="{ '--tag-color': categoryColors[tagCategory(id)] || '#6e8775' }">{{ tagName(id) }} <b>{{ value }}</b></span></div></div>
              <div class="bean-card-foot"><span>{{ coffee.species }} / {{ coffee.variety }}</span><b>查看详情 ↗</b></div>
            </article>
          </div>
          <div v-if="!beanResults.length" class="empty-state"><strong>没有匹配的样本</strong><span>换一个关键词或清除筛选条件。</span></div>
        </section>

        <section v-else-if="view === 'flavors'" class="page-shell page-enter">
          <div class="section-heading"><div><p class="kicker">03 / FLAVOR ANALYSIS</p><h1>风味分析</h1><p>从喜欢的风味，找到值得比较的豆子。</p></div><button class="text-button" @click="resetFlavor">重置筛选 ×</button></div>
          <FlavorExplorer :tags="tags" :categories="categories" :colors="categoryColors" :coffees="coffees" :matches="filteredCoffees" :selected-flavor="selectedFlavor" :focus-coffee="comparisonFocusCoffee" :compare-ids="compareIds" @flavor="setFlavor" @compare="compareMatchingSamples" @toggle="toggleCompare" />
          <BeanComparison v-if="compareCoffees.length" :coffees="compareCoffees" :tags="tags" :categories="categories" :profiles="profiles" v-model:preference-id="discovery" :country-label="countryLabel" :selected-flavor="selectedFlavor" @remove="toggleCompare" @clear="compareIds = []" @detail="openBean" @flavor="setFlavor" @coffee-focus="comparisonFocusId = $event" />
          <div class="analysis-results">
            <div class="subheading">
              <div><span class="step-label">B</span><div><h2>匹配样本</h2><p aria-live="polite">{{ filteredCoffees.length }} 款匹配 · 已选 {{ compareCoffees.length }} / 4{{ compareCoffees.length === 4 ? ' · 对比已满' : '' }}</p></div></div>
              <div class="analysis-filters">
                <input v-model="searchQuery" aria-label="搜索对比样本" placeholder="搜索样本" />
                <select v-model="countryFilter" aria-label="筛选对比产国"><option value="all">所有产国</option><option v-for="country in countries" :key="country" :value="country">{{ countryLabel(country) }}</option></select>
                <select v-model="processFilter" aria-label="筛选对比处理法"><option value="all">所有处理法</option><option v-for="process in processes" :key="process" :value="process">{{ process }}</option></select>
              </div>
            </div>
            <div class="sample-strip">
              <button v-for="coffee in filteredCoffees" :key="coffee.id" class="sample-row" :class="{ chosen: compareIds.includes(coffee.id), focused: selectedCoffeeId === coffee.id }" :aria-pressed="compareIds.includes(coffee.id)" :disabled="compareCoffees.length >= 4 && !compareIds.includes(coffee.id)" @click="selectedCoffeeId = coffee.id; toggleCompare(coffee)">
                <span class="sample-check" aria-hidden="true">{{ compareIds.includes(coffee.id) ? '✓' : '+' }}</span><span><b>{{ coffee.name }}</b><small>{{ countryLabel(coffee.country) }} · {{ coffee.region }} · {{ coffee.process }}</small></span><i></i>
              </button>
            </div>
            <div v-if="!filteredCoffees.length" class="empty-state"><strong>没有匹配的样本</strong><span>已选豆子仍保留在对比中。</span></div>
          </div>
        </section>

        <section v-else-if="view === 'guide'" class="page-shell page-enter guide-page"><div class="section-heading"><div><p class="kicker">04 / FIELD NOTES</p><h1>咖啡秘籍</h1><p>从生豆到杯中，建立可以被复现的咖啡知识。</p></div></div><div class="guide-layout"><aside class="guide-sidebar panel-line"><div class="guide-sidebar-intro"><p class="kicker">COFFEE FIELD NOTES</p><h2>咖啡秘籍</h2><p>把咖啡知识拆成可快速浏览的章节，适合项目介绍，也适合新手入门时逐块查看。</p></div><nav class="guide-nav" aria-label="咖啡秘籍章节"><button v-for="(section, sectionIndex) in guideSections" :key="section.title" type="button" :class="{ active: guideSectionIndex === sectionIndex }" :aria-current="guideSectionIndex === sectionIndex ? 'page' : undefined" @click="guideSectionIndex = sectionIndex"><span>{{ String(sectionIndex + 1).padStart(2, '0') }}</span><strong>{{ section.title }}</strong><small>{{ section.summary }}</small></button></nav></aside><div class="guide-sections"><section v-for="(section, sectionIndex) in guideSections" v-show="guideSectionIndex === sectionIndex" :key="section.title" class="guide-section guide-section-active"><div class="guide-section-head"><span class="guide-number">{{ String(sectionIndex + 1).padStart(2, '0') }}</span><div><p class="kicker">KNOWLEDGE / {{ String(sectionIndex + 1).padStart(2, '0') }}</p><h2>{{ section.title }}</h2><p>{{ section.summary }}</p></div></div><div class="guide-cards"><article v-for="(card, cardIndex) in section.cards" :key="card[0]" class="guide-card"><span>{{ String(cardIndex + 1).padStart(2, '0') }}</span><h3>{{ card[0] }}</h3><p>{{ card[1] }}</p></article></div></section></div></div></section>

        <section v-else-if="view === 'tools'" class="page-shell page-enter tools-page">
          <div class="section-heading">
            <div><p class="kicker">05 / COFFEE TOOLS</p><h1>咖啡工具</h1><p>把探索结果带回日常冲煮、测量与记录。</p></div>
            <div class="heading-stat"><strong>04</strong><span>可用工具</span></div>
          </div>
          <div class="tools-dashboard">
            <div class="tools-primary">
              <article class="tool-feature">
                <p class="kicker">BREW LABORATORY / 01</p>
                <h2>冲煮比例计算器</h2>
                <div class="ratio-display"><strong>1 : {{ ratio }}</strong><span>粉水比</span></div>
                <div class="tool-inputs"><label>咖啡粉 <input v-model.number="brew.dose" type="number" min="1" /></label><label>注水量 <input v-model.number="brew.water" type="number" min="1" /></label><label>水温 <input v-model.number="brew.temperature" type="number" min="70" max="100" /></label><label>时间 <input v-model.number="brew.time" type="number" min="30" /></label></div>
                <div class="tool-advice"><b>参数提示</b><span>{{ brewAdvice }}</span></div>
                <button class="primary-button" @click="go('guide')">查看冲煮知识 <span>↗</span></button>
              </article>
              <article class="tool-note sample-context">
                <p class="kicker">YOUR NEXT CUP</p><h2>{{ selectedCoffee?.name || '选择一款咖啡样本' }}</h2>
                <p>{{ selectedCoffee ? `${countryLabel(selectedCoffee.country)} · ${selectedCoffee.region} · ${selectedCoffee.process}` : '在风味分析中选择样本后，这里会保留你的探索上下文。' }}</p>
                <div v-if="selectedCoffee" class="context-tags"><span v-for="([id, value]) in topFlavors(selectedCoffee, 4)" :key="id">{{ tagName(id) }} {{ value }}</span></div>
                <button class="line-button" @click="go('flavors')">打开风味分析 →</button>
              </article>
            </div>
            <div class="tool-card-grid">
              <article class="tool-card">
                <p class="kicker">BREW TIMER / 02</p><h3>冲煮计时器</h3>
                <div class="timer-display">{{ timerDisplay }}</div>
                <div class="timer-progress" aria-label="冲煮进度"><i :style="{ width: `${timerProgress}%` }"></i></div>
                <p class="tool-helper">目标时间 {{ brew.time }} 秒</p>
                <div class="tool-card-actions"><button class="primary-button" @click="toggleBrewTimer">{{ brewTimerRunning ? '暂停' : '开始' }}</button><button class="text-button" @click="resetBrewTimer">重置</button></div>
              </article>
              <article class="tool-card">
                <p class="kicker">EXTRACTION / 03</p><h3>萃取率估算</h3>
                <div class="compact-inputs"><label>咖啡粉 <input v-model.number="extraction.dose" type="number" min="1" step="0.1" /></label><label>饮品重量 <input v-model.number="extraction.beverage" type="number" min="1" step="0.1" /></label><label>TDS % <input v-model.number="extraction.tds" type="number" min="0.1" step="0.1" /></label></div>
                <div class="metric-output"><strong>{{ extractionYield }}%</strong><span :class="`metric-status ${extractionStatus.tone}`">{{ extractionStatus.label }}</span></div><p class="tool-helper">{{ extractionStatus.hint }}</p>
              </article>
              <article class="tool-card">
                <p class="kicker">CONVERTER / 04</p><h3>单位换算器</h3>
                <label class="select-label">换算类型<select v-model="converter.type"><option value="mass">质量：克 → 盎司</option><option value="temperature">温度：摄氏 → 华氏</option><option value="volume">体积：毫升 → 液体盎司</option></select></label>
                <label class="converter-input">输入数值<input v-model.number="converter.value" type="number" step="0.1" /></label><output class="converter-result">{{ converterResult }}</output>
              </article>
              <article class="tool-card cupping-card">
                <div class="tool-card-heading"><div><p class="kicker">CUPPING NOTE / 05</p><h3>杯测记录</h3></div><strong>{{ cuppingTotal }} / 50</strong></div>
                <div class="cupping-grid"><label>香气 <input v-model.number="cuppingForm.aroma" type="number" min="0" max="10" /></label><label>酸质 <input v-model.number="cuppingForm.acidity" type="number" min="0" max="10" /></label><label>甜感 <input v-model.number="cuppingForm.sweetness" type="number" min="0" max="10" /></label><label>醇厚度 <input v-model.number="cuppingForm.body" type="number" min="0" max="10" /></label><label>余韵 <input v-model.number="cuppingForm.aftertaste" type="number" min="0" max="10" /></label></div>
                <div class="cupping-average"><span>平均分</span><b>{{ cuppingAverage }}</b></div><textarea v-model="cuppingForm.notes" rows="2" placeholder="记录香气、口感和余韵"></textarea><div class="tool-card-actions"><button class="primary-button" @click="saveCuppingNote">保存记录</button><span v-if="cuppingSaved" class="saved-feedback">已保存</span></div>
              </article>
            </div>
          </div>
        </section>

        <section v-else-if="view === 'login'" class="account-page page-enter"><div class="auth-layout"><div class="auth-intro"><p class="kicker">YOUR COFFEE ACCOUNT</p><h1>保留你的<br /><em>探索轨迹。</em></h1><p>保存冲煮参数、杯测记录与喜欢的咖啡样本。研究员后台仅对管理员账户开放。</p></div><form class="auth-form panel-line" @submit.prevent="submitAuth"><div class="auth-tabs"><button type="button" :class="{ active: authMode === 'login' }" @click="authMode = 'login'; authError = ''">登录</button><button type="button" :class="{ active: authMode === 'register' }" @click="authMode = 'register'; authError = ''">注册</button></div><h2>{{ authMode === 'login' ? '欢迎回来' : '创建账户' }}</h2><label>用户名<input v-model="loginForm.username" required minlength="3" autocomplete="username" /></label><label>密码<input v-model="loginForm.password" required minlength="6" type="password" autocomplete="current-password" /></label><p v-if="authError" class="form-error">{{ authError }}</p><button class="primary-button" :disabled="authBusy">{{ authBusy ? '处理中…' : authMode === 'login' ? '登录账户' : '注册账户' }} <span>↗</span></button></form></div></section>
        <section v-else-if="view === 'account'" class="page-shell page-enter"><div class="section-heading"><div><p class="kicker">MY COFFEE ACCOUNT</p><h1>个人账户</h1><p>你的探索记录与研究权限都集中在这里。</p></div><button class="text-button" @click="logout">退出账户</button></div><div class="account-grid"><article class="account-profile panel-line"><span class="profile-avatar">{{ currentUser?.username?.slice(0, 1).toUpperCase() }}</span><p class="kicker">SIGNED IN AS</p><h2>{{ currentUser?.username }}</h2><p>{{ isAdmin ? '管理员账户 · 研究员权限已开启' : '探索者账户 · 可保存个人记录' }}</p></article><article v-if="isAdmin" class="account-admin panel-line"><p class="kicker">RESEARCH WORKSPACE</p><h2>研究员后台</h2><p>维护咖啡样本和风味标签。所有改动直接写入 SQLite 数据库。</p><div><button class="line-button" @click="go('samples')">维护样本 →</button><button class="line-button" @click="go('tags')">维护标签 →</button></div></article><article class="account-admin panel-line"><p class="kicker">CONTINUE EXPLORING</p><h2>继续上一段路径</h2><p>回到风味分析，查看你刚刚选择的样本。</p><button class="line-button" @click="go('flavors')">返回风味分析 →</button></article></div></section>
        <section v-else-if="view === 'samples' && isAdmin" class="page-shell page-enter admin-page">
          <div class="section-heading"><div><p class="kicker">RESEARCH WORKSPACE / SAMPLES</p><h1>维护样本数据</h1><p>新增样本后会直接保存到 SQLite 数据库，并同步到地图、豆库和风味分析。</p></div><button class="text-button" @click="go('account')">返回账户</button></div>
          <form class="admin-form panel-line" @submit.prevent="createAdminSample"><h2>添加咖啡样本</h2><div class="admin-fields"><label>样本名称<input v-model="adminSampleForm.name" required /></label><label>产国<input v-model="adminSampleForm.country" required /></label><label>代表区域<input v-model="adminSampleForm.region" required /></label><label>品种<input v-model="adminSampleForm.variety" /></label><label>处理法<select v-model="adminSampleForm.process"><option v-for="process in processes" :key="process">{{ process }}</option></select></label><label>烘焙度<input v-model="adminSampleForm.roast" required /></label><label>纬度<input v-model="adminSampleForm.latitude" type="number" step="any" required /></label><label>经度<input v-model="adminSampleForm.longitude" type="number" step="any" required /></label></div><label>样本描述<textarea v-model="adminSampleForm.description" rows="3"></textarea></label><p v-if="adminError" class="form-error">{{ adminError }}</p><button class="primary-button" :disabled="adminBusy">{{ adminBusy ? '保存中…' : '保存到数据库' }} <span>↗</span></button></form>
          <div class="admin-table panel-line"><div class="admin-table-head"><h2>现有样本 <small>{{ coffees.length }} 款</small></h2><button class="text-button" @click="load">刷新数据</button></div>
            <template v-for="coffee in coffees" :key="coffee.id">
              <div class="admin-row admin-sample-row"><span>{{ countryLabel(coffee.country) }}</span><b>{{ coffee.name }}</b><small>{{ coffee.region }} · {{ coffee.process }}</small><div class="admin-row-actions"><button class="text-button" :aria-expanded="adminImageSampleId === coffee.id" @click="adminImageSampleId = adminImageSampleId === coffee.id ? null : coffee.id">{{ coffee.imageUrl ? '管理图片' : '添加图片' }}</button><button class="delete-button" @click="deleteAdminSample(coffee.id)">删除</button></div></div>
              <SampleImageEditor v-if="adminImageSampleId === coffee.id" :coffee="coffee" @saved="saveSampleImage" />
            </template>
          </div>
        </section>
        <section v-else-if="view === 'tags'" class="page-shell page-enter admin-page"><div class="section-heading"><div><p class="kicker">RESEARCH WORKSPACE / FLAVOR TAGS</p><h1>维护风味标签</h1><p>维护前台风味轮盘、筛选和样本描述使用的统一标签。</p></div><button class="text-button" @click="go('account')">返回账户</button></div><form class="admin-form panel-line" @submit.prevent="createAdminTag"><h2>添加风味标签</h2><div class="admin-fields"><label>标签名称<input v-model="adminTagForm.name" required /></label><label>所属大类<select v-model="adminTagForm.category" required><option value="" disabled>选择大类</option><option v-for="category in categories" :key="category.name" :value="category.name">{{ category.name }}</option></select></label></div><label>标签描述<textarea v-model="adminTagForm.description" rows="3"></textarea></label><p v-if="adminError" class="form-error">{{ adminError }}</p><button class="primary-button" :disabled="adminBusy">{{ adminBusy ? '保存中…' : '保存标签' }} <span>↗</span></button></form><div class="admin-table panel-line"><div class="admin-table-head"><h2>现有标签 <small>{{ tags.length }} 个</small></h2></div><div class="admin-row" v-for="tag in tags" :key="tag.id"><span>{{ tag.category }}</span><b>{{ tag.name }}</b><small>{{ tag.description }}</small><button class="delete-button" @click="deleteAdminTag(tag.id)">删除</button></div></div></section>
      </template>
    </main>

    <footer><span>COFFEE FLAVOR ATLAS / 数据驱动的咖啡探索</span><span>LOCAL RESEARCH EDITION · 2025—26</span></footer>

    <div v-if="modalCoffee" class="modal-backdrop" @click.self="closeModal">
      <article class="bean-modal" role="dialog" aria-modal="true" aria-labelledby="bean-detail-title" @keydown.esc="closeModal">
        <button class="modal-close" @click="closeModal" aria-label="关闭">×</button>
        <BeanImage v-if="modalCoffee.imageUrl" :coffee="modalCoffee" class="bean-detail-image" />
        <p class="kicker">SAMPLE PROFILE / {{ countryLabel(modalCoffee.country) }}</p><h2 id="bean-detail-title">{{ modalCoffee.name }}</h2><p class="modal-lede">{{ modalCoffee.description }}</p>
        <div class="modal-meta"><span><small>产区</small><b>{{ modalCoffee.region }}</b></span><span><small>品种</small><b>{{ modalCoffee.variety }}</b></span><span><small>处理法</small><b>{{ modalCoffee.process }}</b></span><span><small>海拔</small><b>{{ modalCoffee.altitude || '—' }}</b></span></div>
        <div class="modal-flavors"><p class="kicker">FLAVOR PROFILE</p><div v-for="([id, value]) in topFlavors(modalCoffee, 6)" :key="id" class="modal-flavor"><span>{{ tagName(id) }}</span><i><b :style="{ width: pct(value), background: categoryColors[tagCategory(id)] || '#6e8775' }"></b></i><em>{{ value }} / 5</em></div></div>
        <section class="reviews-block">
          <div class="reviews-head"><div><p class="kicker">COMMUNITY REVIEWS</p><h3>{{ reviewSummary.average ? reviewSummary.average.toFixed(1) : '—' }} / 5</h3></div><span>{{ reviewSummary.count }} 条评价</span></div>
          <form v-if="currentUser" class="review-form" @submit.prevent="submitReview"><label>评分<select v-model.number="reviewForm.rating"><option :value="5">5 / 5</option><option :value="4">4 / 5</option><option :value="3">3 / 5</option><option :value="2">2 / 5</option><option :value="1">1 / 5</option></select></label><label>评价内容<textarea v-model="reviewForm.content" minlength="2" maxlength="500" required rows="3" placeholder="记录你的香气、口感和余韵"></textarea></label><p v-if="reviewError" class="form-error">{{ reviewError }}</p><button class="primary-button" :disabled="reviewBusy">{{ reviewBusy ? '提交中…' : '提交评价' }} <span>↗</span></button></form>
          <button v-else class="line-button" @click="closeModal(); go('login')">登录后评价 →</button>
          <div v-if="reviews.length" class="review-list"><article v-for="review in reviews" :key="review.id" class="review-item"><div><strong>{{ review.username }}</strong><span>{{ review.rating }} / 5</span></div><p>{{ review.content }}</p><time>{{ review.createdAt }}</time></article></div><p v-else class="review-empty">还没有评价，成为第一个记录这款咖啡的人。</p>
        </section>
        <div class="modal-actions"><button class="line-button" :disabled="compareCoffees.length >= 4 && !compareIds.includes(modalCoffee.id)" @click="compareBean(modalCoffee)">{{ compareIds.includes(modalCoffee.id) ? '查看风味对比 →' : compareCoffees.length >= 4 ? '对比已满（4/4）' : '加入风味对比 →' }}</button><button class="line-button" @click="visitBeanOrigin(modalCoffee)">查看产地 →</button></div>
      </article>
    </div>
  </div>
</template>
