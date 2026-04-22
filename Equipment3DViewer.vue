<template>
  <div class="eq3d-root" ref="rootEl">
    <!-- Topbar -->
    <header class="eq3d-topbar">
      <span class="eq3d-logo">SPARE<span class="eq3d-logo-accent">PART</span><sub class="eq3d-logo-sub">3D</sub></span>
      <div class="eq3d-pill" :class="isEditor ? 'editor' : 'viewer'">{{ isEditor ? 'EDITOR' : 'VIEWER' }}</div>
      <span class="eq3d-project-name">{{ config.projectName || equipmentName || 'Untitled' }}</span>
      <div class="eq3d-toolbar-right">
        <button class="eq3d-tbtn" @click="resetCam">Reset View</button>
        <button class="eq3d-tbtn" @click="toggleHotspots">{{ hotspotsVisible ? 'Hotspots' : 'Hotspots Off' }}</button>
        <button v-if="!isEditor" class="eq3d-tbtn acc" @click="openCart">Cart<span class="eq3d-cbadge" v-show="cartCount > 0">{{ cartCount }}</span></button>
      </div>
    </header>

    <!-- Main layout -->
    <div class="eq3d-main">
      <!-- Viewport -->
      <div class="eq3d-viewport" ref="vpEl">
        <!-- Loader -->
        <div class="eq3d-loader" :class="{ done: modelLoaded }">
          <div class="eq3d-lring"></div>
          <div class="eq3d-ltxt">{{ loadingText }}</div>
          <div v-if="loadError" class="eq3d-lerr">{{ loadError }}</div>
        </div>
        <canvas ref="canvasEl" class="eq3d-canvas"></canvas>
        <div v-show="gridVisible" class="eq3d-grid-ov"></div>
        <div v-show="bracketsVisible" class="eq3d-hc tl"></div>
        <div v-show="bracketsVisible" class="eq3d-hc tr"></div>
        <div v-show="bracketsVisible" class="eq3d-hc bl"></div>
        <div v-show="bracketsVisible" class="eq3d-hc br"></div>
        <div class="eq3d-vptop">{{ isEditor ? 'EDITOR MODE · SHIFT+CLICK MODEL TO PLACE HOTSPOT' : 'CLICK HOTSPOTS TO INSPECT' }}</div>

        <!-- Hotspots container -->
        <div class="eq3d-hotspot-container" ref="hotspotContainer" v-show="hotspotsVisible">
          <div
            v-for="(comp, idx) in config.components"
            :key="comp.id"
            class="eq3d-hotspot"
            :class="getHotspotClass(comp.id)"
            :style="getHotspotStyle(comp.id)"
            @click.stop="onHotspotClick(comp.id)"
            @mousedown.prevent.stop="isEditor ? startHotspotDrag($event, comp) : null"
          >
            <div class="eq3d-hotspot-dot">
              <div class="eq3d-ring"></div>
              <div class="eq3d-ring2"></div>
              <div class="eq3d-core">{{ idx + 1 }}</div>
            </div>
            <div class="eq3d-hotspot-label">{{ comp.label }}</div>
          </div>
        </div>

        <!-- Info popup -->
        <div class="eq3d-info-popup" :class="{ show: activePopupId }" :style="popupStyle" v-if="activePopupComp">
          <div class="eq3d-ip-hd">
            <span class="eq3d-ip-badge">{{ activePopupComp.label }}</span>
            <button class="eq3d-ip-close" @click="closeInfoPopup">&#10005;</button>
          </div>
          <div class="eq3d-ip-title">{{ activePopupComp.label }}</div>
          <div class="eq3d-ip-desc">{{ activePopupComp.desc || '' }}</div>
          <div class="eq3d-ip-specs">
            <div v-for="(s, i) in (activePopupComp.specs || [])" :key="i" class="eq3d-ip-spec">
              <div class="eq3d-ips-lbl">{{ s[0] }}</div>
              <div class="eq3d-ips-val">{{ s[1] }}</div>
            </div>
          </div>
          <div class="eq3d-ip-action">
            <button class="eq3d-ip-btn" @click="viewSpareParts(activePopupComp.id)">View Spare Parts ({{ (activePopupComp.parts || []).length }})</button>
          </div>
        </div>

        <!-- Viewport toolbar -->
        <div class="eq3d-vp-toolbar">
          <div class="eq3d-vpt-group">
            <button class="eq3d-vpt-btn" :class="{ on: gridVisible }" @click="toggleGrid" title="Toggle Grid">
              <svg viewBox="0 0 24 24"><path d="M3 3h18v18H3zM3 9h18M3 15h18M9 3v18M15 3v18"/></svg>
            </button>
            <button class="eq3d-vpt-btn" :class="{ on: bracketsVisible }" @click="toggleBrackets" title="Toggle Brackets">
              <svg viewBox="0 0 24 24"><path d="M3 3h5v2H5v14h3v2H3zM16 3h5v2h-3v14h3v2h-5z"/></svg>
            </button>
            <button class="eq3d-vpt-btn" :class="{ on: colorPickerOpen }" @click="colorPickerOpen = !colorPickerOpen" title="Background Color">
              <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M12 3a9 9 0 010 18V3z" fill="currentColor" opacity=".3"/></svg>
            </button>
          </div>
          <div class="eq3d-vpt-group">
            <div class="eq3d-view-cube">
              <div class="eq3d-vc-empty"></div><button class="eq3d-vc-btn" @click="setView('top')">Top</button><div class="eq3d-vc-empty"></div>
              <button class="eq3d-vc-btn" @click="setView('left')">L</button><button class="eq3d-vc-btn" @click="setView('front')">F</button><button class="eq3d-vc-btn" @click="setView('right')">R</button>
              <div class="eq3d-vc-empty"></div><button class="eq3d-vc-btn" @click="setView('bottom')">Bot</button><div class="eq3d-vc-empty"></div>
            </div>
          </div>
          <div class="eq3d-vpt-group">
            <button class="eq3d-vc-btn" style="width:98px;padding:7px 0;border-radius:0;font-size:9px" @click="setView('back')">Back</button>
          </div>
        </div>

        <!-- Color picker popup -->
        <div class="eq3d-color-popup" :class="{ show: colorPickerOpen }" ref="colorPopupEl">
          <div class="eq3d-vpc-label">Background Color</div>
          <div class="eq3d-vpc-row">
            <div
              v-for="c in bgPresets"
              :key="c"
              class="eq3d-vpc-swatch"
              :class="{ sel: bgColor === c }"
              :style="{ background: c }"
              @click="setBgColor(c)"
            ></div>
          </div>
          <div class="eq3d-vpc-custom">
            <input type="color" :value="bgColor" @input="setBgColor($event.target.value)">
            <span>Custom</span>
          </div>
        </div>

        <!-- Controls hint -->
        <div class="eq3d-chint">
          <div class="eq3d-hi"><span class="eq3d-hk">Drag</span>Rotate</div>
          <div class="eq3d-hi"><span class="eq3d-hk">Scroll</span>Zoom</div>
          <div class="eq3d-hi"><span class="eq3d-hk">{{ isEditor ? 'Shift+Click' : 'Right' }}</span>{{ isEditor ? 'Place Hotspot' : 'Pan' }}</div>
        </div>
      </div>

      <!-- Right Panel -->
      <div class="eq3d-rpanel">
        <!-- Viewer: Idle state (component tree) -->
        <div v-if="!isEditor && !selectedCompId" class="eq3d-pst active">
          <div class="eq3d-idle-hd">
            <h4>Equipment Components</h4>
            <p>Click a hotspot or search below</p>
          </div>
          <div class="eq3d-search-wrap">
            <input class="eq3d-search-input" v-model="searchQuery" type="text" placeholder="Search components or parts...">
          </div>
          <div v-if="searchQuery.trim()" class="eq3d-search-results">
            <div v-if="searchResults.length === 0" class="eq3d-sr-empty">No results for "{{ searchQuery }}"</div>
            <div v-for="r in searchResults" :key="r.comp.id + r.label" class="eq3d-sr-item" @click="searchSelect(r.comp.id, r.type)">
              <div class="eq3d-sr-dot" :style="{ background: r.color }"></div>
              <div class="eq3d-sr-info">
                <div class="eq3d-sr-name">{{ r.label }}</div>
                <div class="eq3d-sr-sub">{{ r.sub }}</div>
              </div>
              <span class="eq3d-sr-tag" :class="r.type === 'comp' ? 'comp' : 'part'">{{ r.type === 'comp' ? 'COMP' : 'PART' }}</span>
            </div>
          </div>
          <div v-else class="eq3d-ptree">
            <div v-for="comp in config.components" :key="comp.id" class="eq3d-tgrp">
              <div class="eq3d-tghd" :class="{ open: openGroups[comp.id] }" @click="openGroups[comp.id] = !openGroups[comp.id]">
                <span class="eq3d-chev">&#9654;</span>
                <div class="eq3d-tdot" :style="{ background: comp.hc }"></div>
                {{ comp.label }}
                <span class="eq3d-tcnt">{{ (comp.parts || []).length }}</span>
              </div>
              <div class="eq3d-titems" :class="{ open: openGroups[comp.id] }">
                <div class="eq3d-titem" @click="selPart(comp.id)">
                  <div class="eq3d-tidot" :style="{ background: comp.hc }"></div>
                  <span style="flex:1">View Spare Parts</span>
                  <span class="eq3d-ticnt">{{ (comp.parts || []).length }} parts</span>
                </div>
              </div>
            </div>
          </div>
          <div class="eq3d-cfoot">
            <div class="eq3d-crow">
              <div class="eq3d-cico">
                <svg width="21" height="21" viewBox="0 0 24 24" fill="none" stroke="#6b7280" stroke-width="2"><circle cx="9" cy="21" r="1"/><circle cx="20" cy="21" r="1"/><path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6"/></svg>
                <span class="eq3d-cfb" v-show="cartCount > 0">{{ cartCount }}</span>
              </div>
              <div class="eq3d-clbl">Cart Total</div>
              <div class="eq3d-ctot">${{ cartTotal.toLocaleString() }}</div>
            </div>
            <button class="eq3d-obtn" @click="openCart">View Order Cart</button>
          </div>
        </div>

        <!-- Viewer: Selected component state -->
        <div v-if="!isEditor && selectedCompId" class="eq3d-pst active">
          <div class="eq3d-selhd">
            <button class="eq3d-bk" @click="clearSel">&larr; Back to Components</button>
            <div class="eq3d-spbadge">{{ selectedComp.label }}</div>
            <div class="eq3d-spname">{{ selectedComp.label }}</div>
            <div class="eq3d-spdesc">{{ selectedComp.desc || '' }}</div>
            <div class="eq3d-spgrid">
              <div v-for="(s, i) in (selectedComp.specs || [])" :key="i" class="eq3d-spitem">
                <div class="eq3d-splbl">{{ s[0] }}</div>
                <div class="eq3d-spval">{{ s[1] }}</div>
              </div>
            </div>
          </div>
          <div class="eq3d-spbody">
            <template v-for="cat in selectedPartCategories" :key="cat">
              <div class="eq3d-slbl">{{ cat }}</div>
              <div v-for="p in selectedPartsByCategory(cat)" :key="p.sku" class="eq3d-pcard" :class="{ added: cart[p.sku] }">
                <div class="eq3d-pctop">
                  <div class="eq3d-pcinf">
                    <div class="eq3d-pcname">{{ p.name }}</div>
                    <div class="eq3d-pcsku">{{ p.sku }}</div>
                  </div>
                  <div class="eq3d-pcprice">${{ p.price.toLocaleString() }}</div>
                </div>
                <div class="eq3d-pcbot">
                  <div class="eq3d-sbadge">
                    <div class="eq3d-sdot" :style="{ background: stockColor(p.stock) }"></div>
                    <span :style="{ color: stockColor(p.stock), fontSize: '10px' }">{{ stockLabel(p.stock) }}</span>
                  </div>
                  <div class="eq3d-qrow">
                    <button class="eq3d-qbtn" @click="changeQty(p.sku, -1)">-</button>
                    <span class="eq3d-qnum">{{ partQty(p.sku) }}</span>
                    <button class="eq3d-qbtn" @click="changeQty(p.sku, 1)">+</button>
                  </div>
                  <button
                    class="eq3d-abtn"
                    :class="{ added: cart[p.sku] }"
                    :disabled="p.stock === 'out'"
                    @click="addToCart(p.sku, selectedCompId)"
                  >{{ cart[p.sku] ? 'Added' : '+ Add' }}</button>
                </div>
              </div>
            </template>
            <p v-if="!(selectedComp.parts || []).length" style="color:#6b7280;font-size:12px;padding:12px">No spare parts configured for this component.</p>
          </div>
          <div class="eq3d-cfoot">
            <div class="eq3d-crow">
              <div class="eq3d-cico">
                <svg width="21" height="21" viewBox="0 0 24 24" fill="none" stroke="#6b7280" stroke-width="2"><circle cx="9" cy="21" r="1"/><circle cx="20" cy="21" r="1"/><path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6"/></svg>
                <span class="eq3d-cfb" v-show="cartCount > 0">{{ cartCount }}</span>
              </div>
              <div class="eq3d-clbl">Cart Total</div>
              <div class="eq3d-ctot">${{ cartTotal.toLocaleString() }}</div>
            </div>
            <button class="eq3d-obtn" @click="openCart">View Order Cart</button>
          </div>
        </div>

        <!-- Editor panel -->
        <div v-if="isEditor" class="eq3d-pst active">
          <div class="eq3d-idle-hd">
            <h4>Editor — {{ config.projectName || 'Untitled' }}</h4>
            <p>Select a component to edit</p>
          </div>
          <div class="eq3d-search-wrap">
            <input class="eq3d-search-input" v-model="editorSearchQuery" type="text" placeholder="Search components or parts...">
          </div>
          <div v-if="editorSearchQuery.trim()" class="eq3d-search-results">
            <div v-if="editorSearchResults.length === 0" class="eq3d-sr-empty">No results for "{{ editorSearchQuery }}"</div>
            <div v-for="r in editorSearchResults" :key="r.comp.id + r.label" class="eq3d-sr-item" @click="editorSearchSelect(r.comp.id)">
              <div class="eq3d-sr-dot" :style="{ background: r.color }"></div>
              <div class="eq3d-sr-info">
                <div class="eq3d-sr-name">{{ r.label }}</div>
                <div class="eq3d-sr-sub">{{ r.sub }}</div>
              </div>
              <span class="eq3d-sr-tag" :class="r.type === 'comp' ? 'comp' : 'part'">{{ r.type === 'comp' ? 'COMP' : 'PART' }}</span>
            </div>
          </div>
          <div v-else class="eq3d-editor-scroll">
            <!-- Project name -->
            <div class="eq3d-ed-section">
              <div class="eq3d-ed-section-hd">Project</div>
              <div class="eq3d-ed-field">
                <label>Project Name</label>
                <input v-model="config.projectName">
              </div>
            </div>
            <!-- Component list -->
            <div class="eq3d-ed-section">
              <div class="eq3d-ed-section-hd">Components ({{ config.components.length }})</div>
              <div
                v-for="(c, i) in config.components"
                :key="c.id"
                class="eq3d-ed-comp-item"
                :class="{ sel: editorCompId === c.id }"
                @click="editorSelectComp(c.id)"
              >
                <div class="eq3d-ed-comp-dot" :style="{ background: c.hc }"></div>
                <div class="eq3d-ed-comp-name">{{ i + 1 }}. {{ c.label }}</div>
                <div class="eq3d-ed-comp-parts">{{ (c.parts || []).length }}p</div>
              </div>
              <div class="eq3d-ed-btn-row">
                <button class="eq3d-ed-btn primary" @click="editorAddComp">+ Add Component</button>
              </div>
            </div>
            <div class="eq3d-ed-divider"></div>
            <!-- Editor form for selected component -->
            <div v-if="editorCompId && editorComp">
              <div class="eq3d-ed-section">
                <div class="eq3d-ed-section-hd">Component Details</div>
                <div class="eq3d-ed-row">
                  <div class="eq3d-ed-field" style="flex:3">
                    <label>Label</label>
                    <input v-model="editorComp.label">
                  </div>
                  <div class="eq3d-ed-field" style="flex:0 0 54px">
                    <label>Color</label>
                    <input type="color" v-model="editorComp.hc">
                  </div>
                </div>
                <div class="eq3d-ed-field">
                  <label>Description</label>
                  <textarea v-model="editorComp.desc"></textarea>
                </div>
              </div>
              <div class="eq3d-ed-section">
                <div class="eq3d-ed-section-hd">Hotspot Position</div>
                <div class="eq3d-ed-row">
                  <div class="eq3d-ed-field"><label>X</label><input type="number" step="0.01" v-model.number="editorComp.hotspot.x"></div>
                  <div class="eq3d-ed-field"><label>Y</label><input type="number" step="0.01" v-model.number="editorComp.hotspot.y"></div>
                  <div class="eq3d-ed-field"><label>Z</label><input type="number" step="0.01" v-model.number="editorComp.hotspot.z"></div>
                </div>
                <div class="eq3d-ed-hint">Hold Shift + Click on the 3D model to place this hotspot, or drag it directly.</div>
              </div>
              <div class="eq3d-ed-section">
                <div class="eq3d-ed-section-hd">Specs</div>
                <div v-for="(s, i) in (editorComp.specs || [])" :key="i" class="eq3d-ed-spec-row">
                  <input placeholder="Key" v-model="editorComp.specs[i][0]">
                  <input placeholder="Value" v-model="editorComp.specs[i][1]">
                  <button class="eq3d-ed-del-btn" @click="editorComp.specs.splice(i, 1)">&#10005;</button>
                </div>
                <div class="eq3d-ed-btn-row">
                  <button class="eq3d-ed-btn secondary" @click="addEditorSpec">+ Add Spec</button>
                </div>
              </div>
              <div class="eq3d-ed-section">
                <div class="eq3d-ed-section-hd">Spare Parts ({{ (editorComp.parts || []).length }})</div>
                <div v-for="(p, i) in (editorComp.parts || [])" :key="i" class="eq3d-pcard" style="margin-bottom:6px;padding:10px">
                  <div class="eq3d-ed-row" style="margin-bottom:4px">
                    <div class="eq3d-ed-field"><label>Name</label><input v-model="editorComp.parts[i].name"></div>
                    <button class="eq3d-ed-del-btn" style="margin-top:16px" @click="editorComp.parts.splice(i, 1)">&#10005;</button>
                  </div>
                  <div class="eq3d-ed-row">
                    <div class="eq3d-ed-field"><label>SKU</label><input v-model="editorComp.parts[i].sku"></div>
                    <div class="eq3d-ed-field"><label>Category</label><input v-model="editorComp.parts[i].cat"></div>
                  </div>
                  <div class="eq3d-ed-row">
                    <div class="eq3d-ed-field"><label>Price ($)</label><input type="number" v-model.number="editorComp.parts[i].price"></div>
                    <div class="eq3d-ed-field">
                      <label>Stock</label>
                      <select v-model="editorComp.parts[i].stock">
                        <option value="ok">In Stock</option>
                        <option value="low">Low Stock</option>
                        <option value="out">Out of Stock</option>
                      </select>
                    </div>
                  </div>
                </div>
                <div class="eq3d-ed-btn-row">
                  <button class="eq3d-ed-btn secondary" @click="editorAddPart">+ Add Part</button>
                </div>
              </div>
              <div class="eq3d-ed-divider"></div>
              <div class="eq3d-ed-btn-row">
                <button class="eq3d-ed-btn danger" @click="editorDeleteComp">Delete This Component</button>
              </div>
            </div>
            <p v-else style="color:#6b7280;font-size:12px;text-align:center;padding:24px">Click a component above to edit</p>
          </div>
          <div class="eq3d-ed-footer">
            <button class="eq3d-ed-btn green" style="flex:1" @click="editorSave">Save Config</button>
            <button class="eq3d-ed-btn secondary" @click="editorExport">Export JSON</button>
          </div>
        </div>
      </div>
    </div>

    <!-- Cart Modal -->
    <div class="eq3d-ovr" :class="{ open: cartOpen }" @click.self="cartOpen = false">
      <div class="eq3d-modal">
        <div class="eq3d-mhd">
          <h4>Order Cart</h4>
          <button class="eq3d-mcl" @click="cartOpen = false">&#10005;</button>
        </div>
        <div class="eq3d-mbd">
          <p v-if="cartItems.length === 0" style="color:#6b7280;font-size:13px">Cart is empty.</p>
          <table v-else class="eq3d-ctbl">
            <thead><tr><th>Part</th><th>SKU</th><th>Unit</th><th>Qty</th><th>Total</th><th></th></tr></thead>
            <tbody>
              <tr v-for="ci in cartItems" :key="ci.part.sku">
                <td style="font-weight:600;font-size:12px">{{ ci.part.name }}</td>
                <td style="font-family:var(--eq3d-mono);font-size:11px;color:#6b7280">{{ ci.part.sku }}</td>
                <td style="font-family:var(--eq3d-mono)">${{ ci.part.price.toLocaleString() }}</td>
                <td style="font-weight:700;text-align:center">{{ ci.qty }}</td>
                <td style="font-family:var(--eq3d-mono);color:#4f46e5;font-weight:700">${{ (ci.part.price * ci.qty).toLocaleString() }}</td>
                <td><button class="eq3d-rbtn" @click="removeFromCart(ci.part.sku)">&#10005;</button></td>
              </tr>
            </tbody>
            <tfoot>
              <tr style="border-top:2px solid #e5e7eb">
                <td colspan="4" style="padding:10px 8px;font-weight:700;font-size:12px">Order Total</td>
                <td style="padding:10px 8px;font-family:var(--eq3d-mono);font-size:16px;font-weight:700;color:#4f46e5">${{ cartTotal.toLocaleString() }}</td>
                <td></td>
              </tr>
            </tfoot>
          </table>
        </div>
        <div class="eq3d-mft">
          <span style="font-size:13px;color:#6b7280;flex:1;font-weight:500">Total: ${{ cartTotal.toLocaleString() }}</span>
          <button class="eq3d-tbtn" @click="cartOpen = false">Continue</button>
          <button class="eq3d-obtn" style="width:auto;padding:9px 18px;font-size:12px" @click="submitOrder">Submit Order</button>
        </div>
      </div>
    </div>

    <!-- Toasts -->
    <div class="eq3d-toasts">
      <div v-for="t in toasts" :key="t.id" class="eq3d-toast">{{ t.msg }}</div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onBeforeUnmount, watch, nextTick } from "vue";

const props = defineProps({
  modelUrl: { type: String, required: true },
  initialConfig: { type: Object, default: () => ({}) },
  isEditor: { type: Boolean, default: false },
  equipmentName: { type: String, default: "" },
  equipmentId: { type: String, default: "" },
});

const emit = defineEmits(["config-change", "order-submit"]);

// ── Refs ──
const rootEl = ref(null);
const vpEl = ref(null);
const canvasEl = ref(null);
const hotspotContainer = ref(null);
const colorPopupEl = ref(null);

// ── State ──
const config = reactive({
  projectName: "",
  components: [],
});

const modelLoaded = ref(false);
const loadingText = ref("LOADING MODEL");
const loadError = ref("");
const hotspotsVisible = ref(true);
const gridVisible = ref(true);
const bracketsVisible = ref(true);
const colorPickerOpen = ref(false);
const bgColor = ref("#e8ecf1");
const searchQuery = ref("");
const editorSearchQuery = ref("");
const selectedCompId = ref(null);
const editorCompId = ref(null);
const activePopupId = ref(null);
const cartOpen = ref(false);
const cart = reactive({});
const openGroups = reactive({});
const toasts = ref([]);
const hotspotPositions = reactive({});

const bgPresets = ["#e8ecf1","#f1f5f9","#f9fafb","#ffffff","#e2e8f0","#dbeafe","#ede9fe","#d1d5db","#cbd5e1","#94a3b8","#475569","#1e293b"];

// ── Three.js internals (not reactive) ──
let THREE = null;
let renderer = null;
let scene = null;
let camera = null;
let controls = null;
let grid = null;
let loadedModel = null;
let allMeshes = [];
let modelCenter = null;
let modelSize = null;
let camAnim = null;
let animFrameId = null;
let dragState = null;
let partQtys = {};

// ── Computed ──
const selectedComp = computed(() => config.components.find(c => c.id === selectedCompId.value));
const editorComp = computed(() => config.components.find(c => c.id === editorCompId.value));
const activePopupComp = computed(() => activePopupId.value ? config.components.find(c => c.id === activePopupId.value) : null);
const popupStyle = ref({});

const cartItems = computed(() => Object.values(cart));
const cartCount = computed(() => Object.keys(cart).length);
const cartTotal = computed(() => Object.values(cart).reduce((s, c) => s + c.part.price * c.qty, 0));

const selectedPartCategories = computed(() => {
  if (!selectedComp.value) return [];
  return [...new Set((selectedComp.value.parts || []).map(p => p.cat))];
});

const searchResults = computed(() => {
  const q = searchQuery.value.trim().toLowerCase();
  if (!q) return [];
  const results = [];
  config.components.forEach(c => {
    if (c.label.toLowerCase().includes(q) || (c.desc || "").toLowerCase().includes(q)) {
      results.push({ type: "comp", comp: c, label: c.label, sub: c.desc || "Component", color: c.hc });
    }
    (c.parts || []).forEach(p => {
      if (p.name.toLowerCase().includes(q) || p.sku.toLowerCase().includes(q) || (p.cat || "").toLowerCase().includes(q)) {
        results.push({ type: "part", comp: c, label: p.name, sub: `${p.sku} - ${c.label}`, color: c.hc });
      }
    });
  });
  return results;
});

const editorSearchResults = computed(() => {
  const q = editorSearchQuery.value.trim().toLowerCase();
  if (!q) return [];
  const results = [];
  config.components.forEach(c => {
    if (c.label.toLowerCase().includes(q) || (c.desc || "").toLowerCase().includes(q)) {
      results.push({ type: "comp", comp: c, label: c.label, sub: c.desc || "Component", color: c.hc });
    }
    (c.parts || []).forEach(p => {
      if (p.name.toLowerCase().includes(q) || p.sku.toLowerCase().includes(q)) {
        results.push({ type: "part", comp: c, label: p.name, sub: `${p.sku} - ${c.label}`, color: c.hc });
      }
    });
  });
  return results;
});

// ── Methods ──
function selectedPartsByCategory(cat) {
  if (!selectedComp.value) return [];
  return (selectedComp.value.parts || []).filter(p => p.cat === cat);
}

function stockColor(stock) {
  return stock === "ok" ? "#10b981" : stock === "low" ? "#f59e0b" : "#ef4444";
}

function stockLabel(stock) {
  return stock === "ok" ? "In Stock" : stock === "low" ? "Low Stock" : "Out of Stock";
}

function partQty(sku) {
  return cart[sku] ? cart[sku].qty : (partQtys[sku] || 1);
}

function changeQty(sku, delta) {
  if (cart[sku]) {
    cart[sku].qty = Math.max(1, Math.min(99, cart[sku].qty + delta));
  } else {
    partQtys[sku] = Math.max(1, Math.min(99, (partQtys[sku] || 1) + delta));
  }
}

function addToCart(sku, compId) {
  const comp = config.components.find(c => c.id === compId);
  const part = comp?.parts?.find(p => p.sku === sku);
  if (!part || part.stock === "out") return;
  const qty = partQtys[sku] || 1;
  if (cart[sku]) {
    cart[sku].qty += qty;
  } else {
    cart[sku] = { part, qty, cid: compId };
  }
  toast("Added: " + part.name.substring(0, 36));
}

function removeFromCart(sku) {
  delete cart[sku];
}

function openCart() { cartOpen.value = true; }

function submitOrder() {
  const items = Object.values(cart).map(ci => ({
    name: ci.part.name,
    sku: ci.part.sku,
    qty: ci.qty,
    price: ci.part.price,
  }));
  emit("order-submit", items);
  cartOpen.value = false;
  toast("Order submitted successfully");
}

function toast(msg) {
  const id = Date.now();
  toasts.value.push({ id, msg });
  setTimeout(() => { toasts.value = toasts.value.filter(t => t.id !== id); }, 2600);
}

// ── Hotspot helpers ──
function getHotspotClass(id) {
  const cls = {};
  if (activePopupId.value === id || selectedCompId.value === id) {
    cls["active"] = true;
    cls["focused"] = true;
  } else if (activePopupId.value || selectedCompId.value) {
    cls["dimmed"] = true;
  }
  if (props.isEditor && editorCompId.value === id) {
    cls["editor-sel"] = true;
    delete cls["dimmed"];
  }
  const pos = hotspotPositions[id];
  if (pos && pos.behind) cls["behind"] = true;
  return cls;
}

function getHotspotStyle(id) {
  const pos = hotspotPositions[id];
  if (!pos) return { display: "none" };
  return { left: pos.x + "px", top: pos.y + "px" };
}

function onHotspotClick(id) {
  if (props.isEditor) {
    editorSelectComp(id);
    return;
  }
  if (activePopupId.value === id) {
    closeInfoPopup();
    return;
  }
  showInfoPopup(id);
}

function showInfoPopup(id) {
  activePopupId.value = id;
  highlightHotspot(id);
}

function closeInfoPopup() {
  activePopupId.value = null;
}

function viewSpareParts(id) {
  closeInfoPopup();
  selPart(id);
}

function selPart(id) {
  selectedCompId.value = id;
  focusHotspot(id);
  highlightHotspot(id);
}

function clearSel() {
  selectedCompId.value = null;
  searchQuery.value = "";
}

function highlightHotspot(id) {
  // Handled reactively by getHotspotClass
}

function searchSelect(compId) {
  searchQuery.value = "";
  focusHotspot(compId);
  selPart(compId);
}

function editorSearchSelect(compId) {
  editorSearchQuery.value = "";
  focusHotspot(compId);
  editorSelectComp(compId);
}

// ── Viewport controls ──
function toggleGrid() {
  gridVisible.value = !gridVisible.value;
  if (grid) grid.visible = gridVisible.value;
}

function toggleBrackets() {
  bracketsVisible.value = !bracketsVisible.value;
}

function toggleHotspots() {
  hotspotsVisible.value = !hotspotsVisible.value;
  if (!hotspotsVisible.value) closeInfoPopup();
}

function setBgColor(hex) {
  bgColor.value = hex;
  if (!THREE || !scene || !renderer) return;
  const col = new THREE.Color(hex);
  scene.background = col;
  scene.fog.color = col;
  renderer.setClearColor(col, 1);
}

function resetCam() {
  if (!loadedModel || !THREE) return;
  const box = new THREE.Box3().setFromObject(loadedModel);
  const c = box.getCenter(new THREE.Vector3());
  const s = box.getSize(new THREE.Vector3());
  const d = (Math.max(s.x, s.y, s.z) / 2) / Math.tan(camera.fov * Math.PI / 360) * 1.6;
  controls.target.copy(c);
  camera.position.set(c.x + d * 0.7, c.y + d * 0.5, c.z + d * 0.7);
  controls.update();
  closeInfoPopup();
  clearSel();
}

function setView(name) {
  if (!THREE || !modelCenter) return;
  const c = modelCenter;
  const d = (Math.max(modelSize.x, modelSize.y, modelSize.z) / 2) / Math.tan(camera.fov * Math.PI / 360) * 1.6;
  const target = new THREE.Vector3().copy(c);
  let newPos;
  switch (name) {
    case "front": newPos = new THREE.Vector3(c.x, c.y, c.z + d); break;
    case "back": newPos = new THREE.Vector3(c.x, c.y, c.z - d); break;
    case "left": newPos = new THREE.Vector3(c.x - d, c.y, c.z); break;
    case "right": newPos = new THREE.Vector3(c.x + d, c.y, c.z); break;
    case "top": newPos = new THREE.Vector3(c.x, c.y + d, c.z + 0.01); break;
    case "bottom": newPos = new THREE.Vector3(c.x, c.y - d, c.z + 0.01); break;
    default: return;
  }
  animateCamera(newPos, target, 500);
}

function focusHotspot(id) {
  if (!THREE || !loadedModel) return;
  const comp = config.components.find(c => c.id === id);
  if (!comp) return;
  const target = new THREE.Vector3(comp.hotspot.x, comp.hotspot.y, comp.hotspot.z);
  const camDir = new THREE.Vector3().subVectors(camera.position, controls.target).normalize();
  const dist = Math.max(modelSize.x, modelSize.y, modelSize.z) * 0.45;
  const newCamPos = new THREE.Vector3().copy(target).add(camDir.multiplyScalar(dist));
  animateCamera(newCamPos, target, 600);
}

function animateCamera(newPos, newTarget, duration) {
  const startPos = camera.position.clone();
  const startTarget = controls.target.clone();
  const startTime = performance.now();
  if (camAnim) cancelAnimationFrame(camAnim);
  function step() {
    const t = Math.min((performance.now() - startTime) / duration, 1);
    const ease = t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
    camera.position.lerpVectors(startPos, newPos, ease);
    controls.target.lerpVectors(startTarget, newTarget, ease);
    controls.update();
    if (t < 1) camAnim = requestAnimationFrame(step);
    else camAnim = null;
  }
  step();
}

// ── Update hotspot 2D positions ──
function updateHotspots() {
  if (!hotspotsVisible.value || !canvasEl.value || !camera) return;
  const rect = canvasEl.value.getBoundingClientRect();
  config.components.forEach(comp => {
    const pos = new THREE.Vector3(comp.hotspot.x, comp.hotspot.y, comp.hotspot.z);
    pos.project(camera);
    const behind = pos.z > 1;
    const x = (pos.x * 0.5 + 0.5) * rect.width;
    const y = (-pos.y * 0.5 + 0.5) * rect.height;
    hotspotPositions[comp.id] = { x, y, behind };
  });

  // Update popup position
  if (activePopupId.value) {
    const comp = config.components.find(c => c.id === activePopupId.value);
    if (comp) {
      const pos = new THREE.Vector3(comp.hotspot.x, comp.hotspot.y, comp.hotspot.z);
      pos.project(camera);
      const x = (pos.x * 0.5 + 0.5) * rect.width;
      const y = (-pos.y * 0.5 + 0.5) * rect.height;
      let px = x + 30, py = y - 60;
      if (px + 290 > rect.width - 10) px = x - 320;
      py = Math.max(10, Math.min(py, rect.height - 210));
      popupStyle.value = { left: px + "px", top: py + "px" };
    }
  }
}

// ── Editor ──
function editorSelectComp(id) {
  editorCompId.value = id;
  focusHotspot(id);
}

function editorAddComp() {
  const n = config.components.length + 1;
  const id = "comp_" + Date.now();
  const hx = modelCenter ? modelCenter.x + ((n % 2 === 0 ? 1 : -1) * (modelSize?.x || 2) * 0.2) : 0;
  const hy = modelCenter ? modelCenter.y : 1;
  const hz = modelCenter ? modelCenter.z + ((n % 3 === 0 ? 1 : -1) * (modelSize?.z || 2) * 0.2) : 0;
  config.components.push({
    id,
    label: "Component " + n,
    hc: "#4f46e5",
    hotspot: { x: parseFloat(hx.toFixed(4)), y: parseFloat(hy.toFixed(4)), z: parseFloat(hz.toFixed(4)) },
    desc: "",
    specs: [],
    parts: [],
  });
  editorSelectComp(id);
  toast("Component added — Shift+Click model to place hotspot");
}

function editorAddPart() {
  if (!editorComp.value) return;
  if (!editorComp.value.parts) editorComp.value.parts = [];
  editorComp.value.parts.push({ sku: "NEW-SKU-" + (editorComp.value.parts.length + 1), name: "New Part", cat: "General", price: 0, stock: "ok" });
}

function addEditorSpec() {
  if (!editorComp.value) return;
  if (!editorComp.value.specs) editorComp.value.specs = [];
  editorComp.value.specs.push(["", ""]);
}

function editorDeleteComp() {
  if (!confirm("Delete this component and all its spare parts?")) return;
  config.components = config.components.filter(c => c.id !== editorCompId.value);
  editorCompId.value = null;
  toast("Component deleted");
}

function editorSave() {
  emit("config-change", JSON.parse(JSON.stringify(config)));
  toast("Configuration saved!");
}

function editorExport() {
  const blob = new Blob([JSON.stringify(config, null, 2)], { type: "application/json" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = (config.projectName || "config") + ".json";
  a.click();
  URL.revokeObjectURL(a.href);
  toast("Config exported");
}

// ── Hotspot dragging (editor) ──
function startHotspotDrag(e, comp) {
  if (e.button !== 0 || !props.isEditor) return;
  editorSelectComp(comp.id);
  const rect = canvasEl.value.getBoundingClientRect();
  const hsPos = new THREE.Vector3(comp.hotspot.x, comp.hotspot.y, comp.hotspot.z);
  const camDir = new THREE.Vector3().subVectors(camera.position, controls.target).normalize();
  const plane = new THREE.Plane().setFromNormalAndCoplanarPoint(camDir, hsPos);
  dragState = { comp, plane, rect, moved: false };
  controls.enabled = false;
  document.body.style.cursor = "grabbing";
}

function onDragMove(e) {
  if (!dragState) return;
  e.preventDefault();
  dragState.moved = true;
  const rect = dragState.rect;
  const mx = ((e.clientX - rect.left) / rect.width) * 2 - 1;
  const my = -((e.clientY - rect.top) / rect.height) * 2 + 1;
  const rc = new THREE.Raycaster();
  rc.setFromCamera(new THREE.Vector2(mx, my), camera);
  const hit = new THREE.Vector3();
  if (rc.ray.intersectPlane(dragState.plane, hit)) {
    dragState.comp.hotspot.x = parseFloat(hit.x.toFixed(4));
    dragState.comp.hotspot.y = parseFloat(hit.y.toFixed(4));
    dragState.comp.hotspot.z = parseFloat(hit.z.toFixed(4));
  }
}

function onDragEnd() {
  if (!dragState) return;
  controls.enabled = true;
  document.body.style.cursor = "";
  if (dragState.moved) toast("Hotspot moved");
  dragState = null;
}

// ── Canvas click for editor placement ──
function onCanvasClick(e) {
  if (!e.shiftKey || !editorCompId.value || !props.isEditor) return;
  const rect = canvasEl.value.getBoundingClientRect();
  const mouse = new THREE.Vector2(
    ((e.clientX - rect.left) / rect.width) * 2 - 1,
    -((e.clientY - rect.top) / rect.height) * 2 + 1,
  );
  const rc = new THREE.Raycaster();
  rc.setFromCamera(mouse, camera);
  const hits = rc.intersectObjects(allMeshes, true);
  if (hits.length) {
    const p = hits[0].point;
    const comp = config.components.find(c => c.id === editorCompId.value);
    if (comp) {
      comp.hotspot.x = parseFloat(p.x.toFixed(4));
      comp.hotspot.y = parseFloat(p.y.toFixed(4));
      comp.hotspot.z = parseFloat(p.z.toFixed(4));
      toast(`Hotspot placed at (${p.x.toFixed(2)}, ${p.y.toFixed(2)}, ${p.z.toFixed(2)})`);
    }
  }
}

// ── Auto-distribute hotspots ──
function autoDistributeHotspots(bbox, center, size) {
  const comps = config.components;
  const n = comps.length;
  if (n === 0) return;
  // Only distribute if the first component is at default position
  const f = comps[0].hotspot;
  if (f && !(f.x === 0 && f.y === 1 && f.z === 0)) return;

  for (let i = 0; i < n; i++) {
    const t = n > 1 ? i / (n - 1) : 0.5;
    const y = bbox.min.y + size.y * (0.1 + t * 0.8);
    const xOff = (i % 2 === 0 ? 1 : -1) * size.x * 0.3;
    const zOff = (i % 3 === 0 ? 1 : -1) * size.z * 0.15;
    comps[i].hotspot = { x: center.x + xOff, y, z: center.z + zOff };
  }
}

// ── Three.js init ──
async function loadThreeJS() {
  // Load Three.js from CDN
  await loadScript("https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js");
  await loadScript("https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/loaders/GLTFLoader.js");
  await loadScript("https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js");
  THREE = window.THREE;
}

function loadScript(src) {
  return new Promise((resolve, reject) => {
    // Check if already loaded
    if (document.querySelector(`script[src="${src}"]`)) {
      resolve();
      return;
    }
    const s = document.createElement("script");
    s.src = src;
    s.onload = resolve;
    s.onerror = reject;
    document.head.appendChild(s);
  });
}

function initScene() {
  const canvas = canvasEl.value;
  renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: false });
  renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
  renderer.setClearColor(0xe8ecf1, 1);
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.6;
  renderer.outputEncoding = THREE.sRGBEncoding;

  scene = new THREE.Scene();
  scene.background = new THREE.Color(0xe8ecf1);
  scene.fog = new THREE.FogExp2(0xe8ecf1, 0.006);

  camera = new THREE.PerspectiveCamera(45, 1, 0.01, 1000);
  camera.position.set(5, 4, 6);

  controls = new THREE.OrbitControls(camera, canvas);
  controls.enableDamping = true;
  controls.dampingFactor = 0.08;
  controls.rotateSpeed = 0.8;
  controls.zoomSpeed = 1.0;
  controls.panSpeed = 0.6;
  controls.minDistance = 0.5;
  controls.maxDistance = 100;
  controls.target.set(0, 1, 0);

  // Lights
  scene.add(new THREE.AmbientLight(0xffffff, 0.7));
  const kl = new THREE.DirectionalLight(0xffffff, 1.0);
  kl.position.set(5, 10, 5);
  kl.castShadow = true;
  kl.shadow.mapSize.set(2048, 2048);
  scene.add(kl);
  const l2 = new THREE.DirectionalLight(0x88bbff, 0.5);
  l2.position.set(-6, 4, -3);
  scene.add(l2);
  const l3 = new THREE.DirectionalLight(0xffa040, 0.3);
  l3.position.set(0, -2, -8);
  scene.add(l3);
  scene.add(new THREE.HemisphereLight(0xdbeafe, 0xe8ecf1, 0.6));

  // Grid
  grid = new THREE.GridHelper(30, 60, 0xc7d2de, 0xdde3eb);
  grid.material.opacity = 0.5;
  grid.material.transparent = true;
  scene.add(grid);

  modelCenter = new THREE.Vector3(0, 1, 0);
  modelSize = new THREE.Vector3(4, 4, 4);

  resize();
}

function processModel(gltf) {
  loadedModel = gltf.scene;
  loadedModel.traverse(c => {
    if (c.isMesh) { c.castShadow = true; c.receiveShadow = true; allMeshes.push(c); }
  });
  const box = new THREE.Box3().setFromObject(loadedModel);
  const size = box.getSize(new THREE.Vector3());
  const maxDim = Math.max(size.x, size.y, size.z);
  const s = 4 / maxDim;
  loadedModel.scale.setScalar(s);
  const box2 = new THREE.Box3().setFromObject(loadedModel);
  const c2 = box2.getCenter(new THREE.Vector3());
  loadedModel.position.sub(c2);
  loadedModel.position.y -= box2.min.y - c2.y;
  scene.add(loadedModel);
  const fb = new THREE.Box3().setFromObject(loadedModel);
  const fc = fb.getCenter(new THREE.Vector3());
  const fs = fb.getSize(new THREE.Vector3());
  modelCenter.copy(fc);
  modelSize.copy(fs);
  controls.target.copy(fc);
  const d = (Math.max(fs.x, fs.y, fs.z) / 2) / Math.tan(camera.fov * Math.PI / 360) * 1.6;
  camera.position.set(fc.x + d * 0.7, fc.y + d * 0.5, fc.z + d * 0.7);
  controls.update();
  autoDistributeHotspots(fb, fc, fs);
  modelLoaded.value = true;
  toast("3D model loaded");
}

function loadModel() {
  const loader = new THREE.GLTFLoader();
  loader.load(
    props.modelUrl,
    gltf => processModel(gltf),
    xhr => {
      if (xhr.total > 0) loadingText.value = "LOADING " + Math.round(xhr.loaded / xhr.total * 100) + "%";
    },
    err => {
      loadError.value = "Failed to load 3D model";
      console.error("GLB load error:", err);
    },
  );
}

function resize() {
  if (!vpEl.value || !renderer || !camera) return;
  const r = vpEl.value.getBoundingClientRect();
  renderer.setSize(r.width, r.height);
  camera.aspect = r.width / r.height;
  camera.updateProjectionMatrix();
}

function animate() {
  animFrameId = requestAnimationFrame(animate);
  if (controls) controls.update();
  updateHotspots();
  if (renderer && scene && camera) renderer.render(scene, camera);
}

// ── Lifecycle ──
onMounted(async () => {
  // Init config from props
  if (props.initialConfig && props.initialConfig.components) {
    config.projectName = props.initialConfig.projectName || props.equipmentName || "";
    config.components = JSON.parse(JSON.stringify(props.initialConfig.components));
  } else {
    config.projectName = props.equipmentName || "Untitled";
    config.components = [];
  }

  await loadThreeJS();
  initScene();

  // Event listeners
  window.addEventListener("resize", resize);
  document.addEventListener("mousemove", onDragMove);
  document.addEventListener("mouseup", onDragEnd);
  canvasEl.value.addEventListener("click", onCanvasClick);

  animate();
  loadModel();
});

onBeforeUnmount(() => {
  if (animFrameId) cancelAnimationFrame(animFrameId);
  if (camAnim) cancelAnimationFrame(camAnim);
  window.removeEventListener("resize", resize);
  document.removeEventListener("mousemove", onDragMove);
  document.removeEventListener("mouseup", onDragEnd);
  if (renderer) { renderer.dispose(); renderer = null; }
  if (controls) { controls.dispose(); controls = null; }
  scene = null;
  camera = null;
  loadedModel = null;
  allMeshes = [];
});

// Watch for config prop changes
watch(() => props.initialConfig, (newVal) => {
  if (newVal && newVal.components) {
    config.projectName = newVal.projectName || props.equipmentName || "";
    config.components = JSON.parse(JSON.stringify(newVal.components));
  }
}, { deep: true });
</script>

<style scoped>
/* ── CSS Variables ── */
.eq3d-root {
  --eq3d-bg: #f9fafb;
  --eq3d-panel: #ffffff;
  --eq3d-card: #f3f4f6;
  --eq3d-surface: #f9fafb;
  --eq3d-border: #e5e7eb;
  --eq3d-border-focus: #6366f1;
  --eq3d-primary: #4f46e5;
  --eq3d-primary-light: #6366f1;
  --eq3d-primary-bg: rgba(99,102,241,.08);
  --eq3d-primary-border: rgba(99,102,241,.25);
  --eq3d-orange: #f97316;
  --eq3d-green: #10b981;
  --eq3d-red: #ef4444;
  --eq3d-gold: #f59e0b;
  --eq3d-text: #1f2937;
  --eq3d-text-secondary: #374151;
  --eq3d-muted: #6b7280;
  --eq3d-faint: #9ca3af;
  --eq3d-disp: 'Inter', system-ui, -apple-system, sans-serif;
  --eq3d-mono: 'JetBrains Mono', 'DM Mono', monospace;
  --eq3d-shadow-sm: 0 1px 2px rgba(0,0,0,.05);
  --eq3d-shadow: 0 1px 3px rgba(0,0,0,.1), 0 1px 2px rgba(0,0,0,.06);
  --eq3d-shadow-md: 0 4px 6px -1px rgba(0,0,0,.1), 0 2px 4px -2px rgba(0,0,0,.1);
  --eq3d-shadow-lg: 0 10px 15px -3px rgba(0,0,0,.1), 0 4px 6px -4px rgba(0,0,0,.1);
  --eq3d-shadow-xl: 0 20px 25px -5px rgba(0,0,0,.1), 0 8px 10px -6px rgba(0,0,0,.1);
  --eq3d-radius: 8px;
  --eq3d-radius-lg: 12px;
  --eq3d-radius-xl: 16px;

  height: 100%;
  display: flex;
  flex-direction: column;
  font-family: var(--eq3d-disp);
  color: var(--eq3d-text);
  background: var(--eq3d-bg);
  -webkit-font-smoothing: antialiased;
  overflow: hidden;
}
*, *::before, *::after { box-sizing: border-box; }

/* ── Topbar ── */
.eq3d-topbar { height: 56px; flex-shrink: 0; display: flex; align-items: center; gap: 14px; padding: 0 20px; background: var(--eq3d-panel); border-bottom: 1px solid var(--eq3d-border); position: relative; z-index: 100; box-shadow: var(--eq3d-shadow-sm); }
.eq3d-logo { font-size: 16px; font-weight: 800; letter-spacing: .5px; color: var(--eq3d-text); text-decoration: none; }
.eq3d-logo-accent { color: var(--eq3d-primary); }
.eq3d-logo-sub { font-size: 9px; font-weight: 500; color: var(--eq3d-muted); letter-spacing: 2px; vertical-align: bottom; margin-left: 2px; font-family: var(--eq3d-mono); }
.eq3d-pill { border-radius: 20px; padding: 3px 10px; font-size: 11px; font-weight: 600; letter-spacing: .3px; font-family: var(--eq3d-mono); }
.eq3d-pill.viewer { background: var(--eq3d-primary-bg); border: 1px solid var(--eq3d-primary-border); color: var(--eq3d-primary); }
.eq3d-pill.editor { background: rgba(249,115,22,.1); border: 1px solid rgba(249,115,22,.3); color: var(--eq3d-orange); }
.eq3d-project-name { font-size: 11px; color: var(--eq3d-muted); font-family: var(--eq3d-mono); }
.eq3d-toolbar-right { margin-left: auto; display: flex; gap: 8px; align-items: center; }
.eq3d-tbtn { background: var(--eq3d-panel); border: 1px solid var(--eq3d-border); color: var(--eq3d-text-secondary); border-radius: var(--eq3d-radius); padding: 7px 14px; font-size: 12px; font-weight: 500; cursor: pointer; transition: all .15s; display: flex; align-items: center; gap: 6px; font-family: var(--eq3d-disp); }
.eq3d-tbtn:hover { background: var(--eq3d-card); border-color: #d1d5db; color: var(--eq3d-text); }
.eq3d-tbtn.acc { background: var(--eq3d-primary); color: #fff; border-color: var(--eq3d-primary); font-weight: 600; position: relative; }
.eq3d-tbtn.acc:hover { background: #4338ca; }
.eq3d-cbadge { position: absolute; top: -6px; right: -6px; background: var(--eq3d-orange); color: #fff; border-radius: 10px; font-size: 10px; font-weight: 700; padding: 1px 5px; min-width: 18px; text-align: center; line-height: 1.6; }

/* ── Main Layout ── */
.eq3d-main { flex: 1; display: grid; grid-template-columns: 1fr 400px; overflow: hidden; }

/* ── Viewport ── */
.eq3d-viewport { position: relative; overflow: hidden; background: #e8ecf1; }
.eq3d-canvas { width: 100%; height: 100%; display: block; cursor: grab; }
.eq3d-canvas:active { cursor: grabbing; }
.eq3d-grid-ov { position: absolute; inset: 0; pointer-events: none; background-image: linear-gradient(rgba(99,102,241,.04) 1px, transparent 1px), linear-gradient(90deg, rgba(99,102,241,.04) 1px, transparent 1px); background-size: 40px 40px; }
.eq3d-hc { position: absolute; width: 18px; height: 18px; pointer-events: none; }
.eq3d-hc.tl { top: 14px; left: 14px; border-top: 2px solid var(--eq3d-primary-light); border-left: 2px solid var(--eq3d-primary-light); opacity: .4; }
.eq3d-hc.tr { top: 14px; right: 14px; border-top: 2px solid var(--eq3d-primary-light); border-right: 2px solid var(--eq3d-primary-light); opacity: .4; }
.eq3d-hc.bl { bottom: 14px; left: 14px; border-bottom: 2px solid var(--eq3d-primary-light); border-left: 2px solid var(--eq3d-primary-light); opacity: .4; }
.eq3d-hc.br { bottom: 14px; right: 14px; border-bottom: 2px solid var(--eq3d-primary-light); border-right: 2px solid var(--eq3d-primary-light); opacity: .4; }
.eq3d-vptop { position: absolute; top: 14px; left: 50%; transform: translateX(-50%); font-family: var(--eq3d-mono); font-size: 10px; color: var(--eq3d-faint); letter-spacing: 1.5px; text-transform: uppercase; pointer-events: none; white-space: nowrap; }

/* ── Controls Hint ── */
.eq3d-chint { position: absolute; bottom: 16px; left: 50%; transform: translateX(-50%); display: flex; gap: 14px; pointer-events: none; background: rgba(255,255,255,.88); border: 1px solid var(--eq3d-border); border-radius: 20px; padding: 6px 16px; backdrop-filter: blur(8px); z-index: 10; box-shadow: var(--eq3d-shadow-sm); }
.eq3d-hi { display: flex; align-items: center; gap: 5px; font-size: 10px; color: var(--eq3d-muted); font-family: var(--eq3d-mono); }
.eq3d-hk { background: var(--eq3d-card); border: 1px solid var(--eq3d-border); border-radius: 4px; padding: 2px 6px; font-size: 9px; color: var(--eq3d-text); font-weight: 500; }

/* ── Hotspots ── */
.eq3d-hotspot-container { position: absolute; inset: 0; pointer-events: none; z-index: 20; }
.eq3d-hotspot { position: absolute; pointer-events: auto; cursor: pointer; transform: translate(-50%, -50%); z-index: 21; transition: opacity .2s; }
.eq3d-hotspot.behind { opacity: 0; pointer-events: none; }
.eq3d-hotspot-dot { width: 28px; height: 28px; border-radius: 50%; display: flex; align-items: center; justify-content: center; position: relative; }
.eq3d-ring { position: absolute; inset: -4px; border-radius: 50%; border: 2px solid var(--eq3d-primary-light); opacity: .4; animation: eq3d-hpulse 2.5s ease-in-out infinite; }
.eq3d-ring2 { position: absolute; inset: -10px; border-radius: 50%; border: 1px solid var(--eq3d-primary-light); opacity: .15; animation: eq3d-hpulse 2.5s ease-in-out infinite .6s; }
.eq3d-core { width: 14px; height: 14px; border-radius: 50%; background: var(--eq3d-primary); box-shadow: 0 2px 8px rgba(79,70,229,.4); position: relative; z-index: 1; display: flex; align-items: center; justify-content: center; font-size: 8px; font-weight: 700; color: #fff; font-family: var(--eq3d-mono); }
@keyframes eq3d-hpulse { 0%, 100% { transform: scale(1); opacity: .4; } 50% { transform: scale(1.3); opacity: .1; } }
.eq3d-hotspot.active .eq3d-core { background: var(--eq3d-orange); box-shadow: 0 2px 8px rgba(249,115,22,.4); }
.eq3d-hotspot.active .eq3d-ring { border-color: var(--eq3d-orange); }
.eq3d-hotspot.active .eq3d-ring2 { border-color: var(--eq3d-orange); }
.eq3d-hotspot-label { position: absolute; left: calc(100% + 8px); top: 50%; transform: translateY(-50%); white-space: nowrap; background: rgba(255,255,255,.95); border: 1px solid var(--eq3d-border); border-radius: var(--eq3d-radius); padding: 4px 10px; font-size: 11px; color: var(--eq3d-primary); font-weight: 600; opacity: 0; pointer-events: none; transition: opacity .15s; box-shadow: var(--eq3d-shadow); }
.eq3d-hotspot:hover .eq3d-hotspot-label { opacity: 1; }
.eq3d-hotspot.active .eq3d-hotspot-label { border-color: rgba(249,115,22,.3); color: var(--eq3d-orange); }
.eq3d-hotspot.editor-sel .eq3d-core { background: var(--eq3d-green); box-shadow: 0 2px 8px rgba(16,185,129,.4); }
.eq3d-hotspot.editor-sel .eq3d-ring { border-color: var(--eq3d-green); animation: none; }
.eq3d-hotspot.dimmed { opacity: .25 !important; pointer-events: none; filter: grayscale(.6); }
.eq3d-hotspot.dimmed .eq3d-ring, .eq3d-hotspot.dimmed .eq3d-ring2 { animation: none !important; }
.eq3d-hotspot.focused .eq3d-hotspot-dot { width: 36px; height: 36px; }
.eq3d-hotspot.focused .eq3d-core { width: 20px; height: 20px; font-size: 10px; box-shadow: 0 0 0 4px rgba(249,115,22,.2), 0 2px 8px rgba(249,115,22,.4); }
.eq3d-hotspot.focused .eq3d-ring { inset: -6px; border-width: 2.5px; animation: eq3d-hpulse 1.5s ease-in-out infinite; }
.eq3d-hotspot.focused .eq3d-ring2 { inset: -14px; border-width: 1.5px; }

/* ── Info Popup ── */
.eq3d-info-popup { position: absolute; z-index: 30; pointer-events: auto; background: rgba(255,255,255,.97); border: 1px solid var(--eq3d-border); border-radius: var(--eq3d-radius-lg); width: 290px; backdrop-filter: blur(12px); box-shadow: var(--eq3d-shadow-xl); display: none; animation: eq3d-popIn .2s ease; }
.eq3d-info-popup.show { display: block; }
@keyframes eq3d-popIn { from { opacity: 0; transform: scale(.96) translateY(4px); } to { opacity: 1; transform: none; } }
.eq3d-ip-hd { padding: 12px 14px 10px; border-bottom: 1px solid var(--eq3d-border); display: flex; align-items: center; gap: 8px; }
.eq3d-ip-badge { background: var(--eq3d-primary-bg); border: 1px solid var(--eq3d-primary-border); border-radius: 6px; padding: 2px 8px; font-size: 10px; color: var(--eq3d-primary); font-family: var(--eq3d-mono); font-weight: 600; letter-spacing: .3px; text-transform: uppercase; }
.eq3d-ip-close { margin-left: auto; background: none; border: none; color: var(--eq3d-muted); font-size: 16px; cursor: pointer; line-height: 1; padding: 2px; border-radius: 4px; transition: all .12s; }
.eq3d-ip-close:hover { color: var(--eq3d-text); background: var(--eq3d-card); }
.eq3d-ip-title { padding: 10px 14px 4px; font-size: 15px; font-weight: 700; color: var(--eq3d-text); }
.eq3d-ip-desc { padding: 0 14px 10px; font-size: 12px; color: var(--eq3d-muted); line-height: 1.5; }
.eq3d-ip-specs { display: grid; grid-template-columns: 1fr 1fr; gap: 5px; padding: 0 14px 12px; }
.eq3d-ip-spec { background: var(--eq3d-card); border: 1px solid var(--eq3d-border); border-radius: var(--eq3d-radius); padding: 6px 8px; }
.eq3d-ips-lbl { font-size: 9px; font-weight: 600; text-transform: uppercase; letter-spacing: .8px; color: var(--eq3d-faint); font-family: var(--eq3d-mono); }
.eq3d-ips-val { font-size: 11px; font-weight: 600; color: var(--eq3d-text); font-family: var(--eq3d-mono); }
.eq3d-ip-action { padding: 10px 14px 12px; border-top: 1px solid var(--eq3d-border); }
.eq3d-ip-btn { width: 100%; background: var(--eq3d-primary); border: none; border-radius: var(--eq3d-radius); padding: 8px; font-size: 12px; font-weight: 600; color: #fff; cursor: pointer; transition: all .15s; display: flex; align-items: center; justify-content: center; gap: 6px; font-family: var(--eq3d-disp); }
.eq3d-ip-btn:hover { background: #4338ca; box-shadow: var(--eq3d-shadow-md); }

/* ── Loader ── */
.eq3d-loader { position: absolute; inset: 0; background: var(--eq3d-bg); display: flex; flex-direction: column; align-items: center; justify-content: center; z-index: 50; transition: opacity .4s; }
.eq3d-loader.done { opacity: 0; pointer-events: none; }
.eq3d-lring { width: 40px; height: 40px; border: 3px solid var(--eq3d-border); border-top-color: var(--eq3d-primary); border-radius: 50%; animation: eq3d-spin 1s linear infinite; margin-bottom: 14px; }
@keyframes eq3d-spin { to { transform: rotate(360deg); } }
.eq3d-ltxt { font-size: 12px; color: var(--eq3d-muted); font-family: var(--eq3d-mono); letter-spacing: 1px; font-weight: 500; }
.eq3d-lerr { color: var(--eq3d-red); font-size: 12px; font-family: var(--eq3d-mono); margin-top: 8px; text-align: center; }

/* ── Right Panel ── */
.eq3d-rpanel { background: var(--eq3d-panel); border-left: 1px solid var(--eq3d-border); display: flex; flex-direction: column; overflow: hidden; }
.eq3d-pst { display: none; flex-direction: column; flex: 1; overflow: hidden; }
.eq3d-pst.active { display: flex; }
.eq3d-idle-hd { padding: 20px 18px 16px; border-bottom: 1px solid var(--eq3d-border); }
.eq3d-idle-hd h4 { font-size: 14px; font-weight: 700; color: var(--eq3d-text); margin: 0 0 4px; letter-spacing: -.2px; }
.eq3d-idle-hd p { font-size: 12px; color: var(--eq3d-muted); margin: 0; }

/* ── Search ── */
.eq3d-search-wrap { padding: 10px 14px; border-bottom: 1px solid var(--eq3d-border); flex-shrink: 0; }
.eq3d-search-input { width: 100%; background: var(--eq3d-card); border: 1px solid var(--eq3d-border); border-radius: 20px; padding: 8px 12px 8px 34px; font-size: 12px; color: var(--eq3d-text); outline: none; transition: all .15s; font-family: var(--eq3d-disp); background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='14' height='14' fill='none' stroke='%239ca3af' stroke-width='2'%3E%3Ccircle cx='6' cy='6' r='4.5'/%3E%3Cpath d='M9.5 9.5L13 13'/%3E%3C/svg%3E"); background-repeat: no-repeat; background-position: 12px center; }
.eq3d-search-input:focus { border-color: var(--eq3d-primary); box-shadow: 0 0 0 3px rgba(99,102,241,.1); background-color: #fff; }
.eq3d-search-results { flex: 1; overflow-y: auto; padding: 8px 12px; }
.eq3d-sr-item { display: flex; align-items: center; gap: 10px; padding: 8px 10px; border-radius: var(--eq3d-radius); cursor: pointer; transition: all .12s; font-size: 12px; border: 1px solid transparent; margin-bottom: 2px; }
.eq3d-sr-item:hover { background: var(--eq3d-card); border-color: var(--eq3d-border); }
.eq3d-sr-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.eq3d-sr-info { flex: 1; min-width: 0; }
.eq3d-sr-name { font-weight: 600; color: var(--eq3d-text); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.eq3d-sr-sub { font-size: 10px; color: var(--eq3d-muted); font-family: var(--eq3d-mono); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.eq3d-sr-tag { font-size: 9px; padding: 2px 6px; border-radius: 4px; font-weight: 600; font-family: var(--eq3d-mono); letter-spacing: .3px; flex-shrink: 0; }
.eq3d-sr-tag.comp { background: var(--eq3d-primary-bg); color: var(--eq3d-primary); }
.eq3d-sr-tag.part { background: rgba(249,115,22,.1); color: var(--eq3d-orange); }
.eq3d-sr-empty { text-align: center; padding: 24px; color: var(--eq3d-muted); font-size: 12px; }

/* ── Component Tree ── */
.eq3d-ptree { flex: 1; overflow-y: auto; padding: 12px; }
.eq3d-tgrp { margin-bottom: 3px; }
.eq3d-tghd { display: flex; align-items: center; gap: 8px; padding: 8px 10px; border-radius: var(--eq3d-radius); cursor: pointer; transition: all .12s; user-select: none; font-size: 12px; font-weight: 600; color: var(--eq3d-text); }
.eq3d-tghd:hover { background: var(--eq3d-card); }
.eq3d-chev { font-size: 10px; width: 14px; transition: transform .18s; color: var(--eq3d-faint); display: inline-block; }
.eq3d-tghd.open .eq3d-chev { transform: rotate(90deg); }
.eq3d-tdot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.eq3d-tcnt { margin-left: auto; font-family: var(--eq3d-mono); font-size: 10px; color: var(--eq3d-muted); background: var(--eq3d-card); border: 1px solid var(--eq3d-border); border-radius: 10px; padding: 1px 7px; font-weight: 500; }
.eq3d-titems { display: none; padding-left: 14px; }
.eq3d-titems.open { display: block; }
.eq3d-titem { display: flex; align-items: center; gap: 7px; padding: 7px 10px; border-radius: var(--eq3d-radius); cursor: pointer; transition: all .12s; font-size: 12px; color: var(--eq3d-muted); border: 1px solid transparent; margin-bottom: 2px; font-weight: 500; }
.eq3d-titem:hover { background: var(--eq3d-card); color: var(--eq3d-text); border-color: var(--eq3d-border); }
.eq3d-tidot { width: 6px; height: 6px; border-radius: 50%; flex-shrink: 0; }
.eq3d-ticnt { font-size: 10px; color: var(--eq3d-muted); margin-left: auto; font-family: var(--eq3d-mono); }

/* ── Selected Component Panel ── */
.eq3d-selhd { padding: 16px 18px; border-bottom: 1px solid var(--eq3d-border); background: var(--eq3d-surface); flex-shrink: 0; }
.eq3d-bk { display: flex; align-items: center; gap: 5px; font-size: 12px; color: var(--eq3d-muted); cursor: pointer; margin-bottom: 10px; background: none; border: none; transition: color .12s; font-weight: 500; font-family: var(--eq3d-disp); }
.eq3d-bk:hover { color: var(--eq3d-primary); }
.eq3d-spbadge { display: inline-flex; align-items: center; gap: 5px; background: var(--eq3d-primary-bg); border: 1px solid var(--eq3d-primary-border); border-radius: 6px; padding: 3px 10px; font-size: 10px; color: var(--eq3d-primary); font-family: var(--eq3d-mono); font-weight: 600; letter-spacing: .3px; margin-bottom: 8px; }
.eq3d-spname { font-size: 16px; font-weight: 700; color: var(--eq3d-text); line-height: 1.3; margin-bottom: 4px; letter-spacing: -.2px; }
.eq3d-spdesc { font-size: 12px; color: var(--eq3d-muted); line-height: 1.5; }
.eq3d-spgrid { display: grid; grid-template-columns: 1fr 1fr; gap: 6px; margin-top: 12px; }
.eq3d-spitem { background: var(--eq3d-panel); border: 1px solid var(--eq3d-border); border-radius: var(--eq3d-radius); padding: 8px 10px; }
.eq3d-splbl { font-size: 9px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; color: var(--eq3d-faint); font-family: var(--eq3d-mono); margin-bottom: 2px; }
.eq3d-spval { font-size: 12px; font-weight: 600; color: var(--eq3d-text); font-family: var(--eq3d-mono); }
.eq3d-spbody { flex: 1; overflow-y: auto; padding: 12px; }
.eq3d-slbl { font-size: 10px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; color: var(--eq3d-faint); margin-bottom: 8px; margin-top: 4px; font-family: var(--eq3d-mono); display: flex; align-items: center; gap: 8px; }
.eq3d-slbl::after { content: ''; flex: 1; height: 1px; background: var(--eq3d-border); }

/* ── Part Cards ── */
.eq3d-pcard { background: var(--eq3d-panel); border: 1px solid var(--eq3d-border); border-radius: var(--eq3d-radius-lg); padding: 12px 14px; margin-bottom: 6px; transition: all .15s; box-shadow: var(--eq3d-shadow-sm); }
.eq3d-pcard:hover { border-color: #d1d5db; box-shadow: var(--eq3d-shadow); }
.eq3d-pcard.added { border-color: rgba(16,185,129,.4); background: rgba(16,185,129,.04); }
.eq3d-pctop { display: flex; align-items: flex-start; gap: 8px; margin-bottom: 8px; }
.eq3d-pcinf { flex: 1; min-width: 0; }
.eq3d-pcname { font-size: 13px; font-weight: 600; color: var(--eq3d-text); line-height: 1.3; margin-bottom: 2px; }
.eq3d-pcsku { font-family: var(--eq3d-mono); font-size: 10px; color: var(--eq3d-muted); }
.eq3d-pcprice { font-size: 15px; font-weight: 700; color: var(--eq3d-primary); white-space: nowrap; font-family: var(--eq3d-mono); }
.eq3d-pcbot { display: flex; align-items: center; gap: 8px; }
.eq3d-sbadge { display: flex; align-items: center; gap: 4px; font-size: 10px; font-family: var(--eq3d-mono); flex: 1; }
.eq3d-sdot { width: 6px; height: 6px; border-radius: 50%; }
.eq3d-qrow { display: flex; align-items: center; gap: 4px; }
.eq3d-qbtn { width: 24px; height: 24px; border-radius: 6px; border: 1px solid var(--eq3d-border); background: var(--eq3d-panel); color: var(--eq3d-text); font-size: 13px; cursor: pointer; display: flex; align-items: center; justify-content: center; transition: all .12s; line-height: 1; padding: 0; }
.eq3d-qbtn:hover { border-color: var(--eq3d-primary); color: var(--eq3d-primary); background: var(--eq3d-primary-bg); }
.eq3d-qnum { width: 24px; text-align: center; font-size: 12px; font-weight: 600; font-family: var(--eq3d-mono); }
.eq3d-abtn { height: 28px; border-radius: var(--eq3d-radius); border: none; background: var(--eq3d-primary); color: #fff; cursor: pointer; padding: 0 12px; font-size: 11px; font-weight: 600; display: flex; align-items: center; gap: 4px; transition: all .15s; white-space: nowrap; font-family: var(--eq3d-disp); }
.eq3d-abtn:hover { background: #4338ca; box-shadow: var(--eq3d-shadow-sm); }
.eq3d-abtn.added { background: var(--eq3d-green); }
.eq3d-abtn:disabled { background: var(--eq3d-card); color: var(--eq3d-faint); cursor: not-allowed; border: 1px solid var(--eq3d-border); }

/* ── Cart Footer ── */
.eq3d-cfoot { padding: 14px 16px; border-top: 1px solid var(--eq3d-border); background: var(--eq3d-panel); flex-shrink: 0; }
.eq3d-crow { display: flex; align-items: center; gap: 10px; margin-bottom: 8px; }
.eq3d-cico { position: relative; }
.eq3d-cfb { position: absolute; top: -5px; right: -6px; background: var(--eq3d-orange); color: #fff; border-radius: 10px; font-size: 10px; font-weight: 700; padding: 1px 5px; min-width: 17px; text-align: center; line-height: 1.6; }
.eq3d-clbl { font-size: 12px; color: var(--eq3d-muted); flex: 1; }
.eq3d-ctot { font-size: 18px; font-weight: 700; color: var(--eq3d-text); font-family: var(--eq3d-mono); }
.eq3d-obtn { width: 100%; background: var(--eq3d-primary); border: none; border-radius: var(--eq3d-radius); padding: 10px; font-size: 13px; font-weight: 600; color: #fff; cursor: pointer; transition: all .15s; display: flex; align-items: center; justify-content: center; gap: 7px; box-shadow: var(--eq3d-shadow-sm); font-family: var(--eq3d-disp); }
.eq3d-obtn:hover { background: #4338ca; box-shadow: var(--eq3d-shadow-md); transform: translateY(-1px); }

/* ── Viewport Toolbar ── */
.eq3d-vp-toolbar { position: absolute; top: 12px; right: 12px; display: flex; flex-direction: column; gap: 4px; z-index: 15; pointer-events: auto; }
.eq3d-vpt-group { background: rgba(255,255,255,.92); border: 1px solid var(--eq3d-border); border-radius: var(--eq3d-radius-lg); overflow: hidden; backdrop-filter: blur(10px); box-shadow: var(--eq3d-shadow); }
.eq3d-vpt-btn { display: flex; align-items: center; justify-content: center; width: 34px; height: 32px; background: none; border: none; color: var(--eq3d-muted); cursor: pointer; transition: all .12s; font-size: 12px; font-family: var(--eq3d-mono); font-weight: 600; position: relative; }
.eq3d-vpt-btn:hover { background: var(--eq3d-card); color: var(--eq3d-text); }
.eq3d-vpt-btn.on { color: var(--eq3d-primary); background: var(--eq3d-primary-bg); }
.eq3d-vpt-btn + .eq3d-vpt-btn { border-top: 1px solid var(--eq3d-border); }
.eq3d-vpt-btn svg { width: 14px; height: 14px; stroke: currentColor; fill: none; stroke-width: 2; }
.eq3d-view-cube { display: grid; grid-template-columns: repeat(3, 32px); gap: 1px; background: var(--eq3d-border); border-radius: var(--eq3d-radius-lg); overflow: hidden; border: 1px solid var(--eq3d-border); }
.eq3d-vc-btn { background: rgba(255,255,255,.92); border: none; color: var(--eq3d-muted); cursor: pointer; font-size: 9px; font-family: var(--eq3d-mono); font-weight: 600; letter-spacing: .3px; padding: 7px 0; transition: all .12s; text-transform: uppercase; }
.eq3d-vc-btn:hover { background: var(--eq3d-primary-bg); color: var(--eq3d-primary); }
.eq3d-vc-empty { background: rgba(255,255,255,.92); }

/* ── Color Picker ── */
.eq3d-color-popup { position: absolute; top: 12px; right: 52px; background: rgba(255,255,255,.97); border: 1px solid var(--eq3d-border); border-radius: var(--eq3d-radius-lg); padding: 10px; z-index: 16; display: none; backdrop-filter: blur(10px); box-shadow: var(--eq3d-shadow-lg); }
.eq3d-color-popup.show { display: block; }
.eq3d-vpc-label { font-size: 10px; color: var(--eq3d-muted); font-family: var(--eq3d-mono); font-weight: 600; text-transform: uppercase; letter-spacing: .5px; margin-bottom: 6px; }
.eq3d-vpc-row { display: flex; gap: 4px; margin-bottom: 8px; flex-wrap: wrap; }
.eq3d-vpc-swatch { width: 24px; height: 24px; border-radius: 6px; border: 2px solid transparent; cursor: pointer; transition: all .12s; box-shadow: var(--eq3d-shadow-sm); }
.eq3d-vpc-swatch:hover, .eq3d-vpc-swatch.sel { border-color: var(--eq3d-primary); transform: scale(1.1); }
.eq3d-vpc-custom { display: flex; align-items: center; gap: 6px; }
.eq3d-vpc-custom input[type="color"] { width: 28px; height: 24px; border: 1px solid var(--eq3d-border); border-radius: 6px; cursor: pointer; padding: 2px; background: none; }
.eq3d-vpc-custom span { font-size: 10px; color: var(--eq3d-muted); font-family: var(--eq3d-mono); font-weight: 500; }

/* ── Editor Styles ── */
.eq3d-editor-scroll { flex: 1; overflow-y: auto; padding: 14px; }
.eq3d-ed-section { margin-bottom: 18px; }
.eq3d-ed-section-hd { font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; color: var(--eq3d-faint); margin-bottom: 10px; font-family: var(--eq3d-mono); display: flex; align-items: center; gap: 8px; }
.eq3d-ed-section-hd::after { content: ''; flex: 1; height: 1px; background: var(--eq3d-border); }
.eq3d-ed-field { margin-bottom: 10px; }
.eq3d-ed-field label { display: block; font-size: 10px; font-weight: 600; text-transform: uppercase; letter-spacing: .5px; color: var(--eq3d-muted); font-family: var(--eq3d-mono); margin-bottom: 4px; }
.eq3d-ed-field input, .eq3d-ed-field textarea, .eq3d-ed-field select { width: 100%; background: var(--eq3d-panel); border: 1px solid var(--eq3d-border); border-radius: var(--eq3d-radius); padding: 8px 10px; font-size: 12px; color: var(--eq3d-text); font-family: var(--eq3d-mono); outline: none; transition: all .15s; }
.eq3d-ed-field input:focus, .eq3d-ed-field textarea:focus { border-color: var(--eq3d-primary); box-shadow: 0 0 0 3px rgba(99,102,241,.1); }
.eq3d-ed-field textarea { resize: vertical; min-height: 56px; }
.eq3d-ed-field input[type="color"] { width: 36px; height: 30px; padding: 3px; cursor: pointer; border-radius: var(--eq3d-radius); }
.eq3d-ed-row { display: flex; gap: 8px; }
.eq3d-ed-row .eq3d-ed-field { flex: 1; }
.eq3d-ed-btn { border: none; border-radius: var(--eq3d-radius); padding: 7px 14px; font-size: 12px; font-weight: 600; cursor: pointer; transition: all .15s; display: flex; align-items: center; gap: 5px; font-family: var(--eq3d-disp); }
.eq3d-ed-btn.primary { background: var(--eq3d-primary); color: #fff; }
.eq3d-ed-btn.primary:hover { background: #4338ca; }
.eq3d-ed-btn.secondary { background: var(--eq3d-card); color: var(--eq3d-text); border: 1px solid var(--eq3d-border); }
.eq3d-ed-btn.secondary:hover { background: var(--eq3d-border); }
.eq3d-ed-btn.danger { background: rgba(239,68,68,.08); color: var(--eq3d-red); border: 1px solid rgba(239,68,68,.2); }
.eq3d-ed-btn.danger:hover { background: rgba(239,68,68,.15); }
.eq3d-ed-btn.green { background: var(--eq3d-green); color: #fff; }
.eq3d-ed-btn.green:hover { background: #059669; }
.eq3d-ed-btn-row { display: flex; gap: 6px; flex-wrap: wrap; margin-top: 8px; }
.eq3d-ed-comp-item { background: var(--eq3d-panel); border: 1px solid var(--eq3d-border); border-radius: var(--eq3d-radius); padding: 10px 12px; margin-bottom: 4px; cursor: pointer; display: flex; align-items: center; gap: 10px; transition: all .12s; font-size: 12px; box-shadow: var(--eq3d-shadow-sm); }
.eq3d-ed-comp-item:hover { border-color: #d1d5db; box-shadow: var(--eq3d-shadow); }
.eq3d-ed-comp-item.sel { border-color: var(--eq3d-primary); background: var(--eq3d-primary-bg); box-shadow: 0 0 0 3px rgba(99,102,241,.1); }
.eq3d-ed-comp-dot { width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }
.eq3d-ed-comp-name { flex: 1; font-weight: 600; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.eq3d-ed-comp-parts { font-size: 10px; color: var(--eq3d-muted); font-family: var(--eq3d-mono); }
.eq3d-ed-spec-row { display: flex; gap: 6px; margin-bottom: 5px; align-items: center; }
.eq3d-ed-spec-row input { flex: 1; background: var(--eq3d-panel); border: 1px solid var(--eq3d-border); border-radius: 6px; padding: 6px 8px; font-size: 11px; color: var(--eq3d-text); font-family: var(--eq3d-mono); outline: none; transition: all .15s; }
.eq3d-ed-spec-row input:focus { border-color: var(--eq3d-primary); box-shadow: 0 0 0 3px rgba(99,102,241,.1); }
.eq3d-ed-del-btn { width: 22px; height: 22px; border-radius: 6px; border: 1px solid var(--eq3d-border); background: var(--eq3d-panel); color: var(--eq3d-muted); cursor: pointer; font-size: 12px; flex-shrink: 0; display: flex; align-items: center; justify-content: center; transition: all .12s; }
.eq3d-ed-del-btn:hover { color: var(--eq3d-red); border-color: rgba(239,68,68,.3); background: rgba(239,68,68,.06); }
.eq3d-ed-hint { font-size: 10px; color: var(--eq3d-muted); margin-top: 5px; line-height: 1.5; font-style: italic; }
.eq3d-ed-divider { height: 1px; background: var(--eq3d-border); margin: 14px 0; }
.eq3d-ed-footer { padding: 12px 14px; border-top: 1px solid var(--eq3d-border); display: flex; gap: 6px; flex-shrink: 0; }

/* ── Cart Modal ── */
.eq3d-ovr { display: none; position: fixed; inset: 0; background: rgba(0,0,0,.3); z-index: 500; align-items: center; justify-content: center; padding: 20px; backdrop-filter: blur(4px); }
.eq3d-ovr.open { display: flex; }
.eq3d-modal { background: var(--eq3d-panel); border: 1px solid var(--eq3d-border); border-radius: var(--eq3d-radius-xl); width: 100%; max-width: 680px; max-height: 84vh; display: flex; flex-direction: column; overflow: hidden; box-shadow: var(--eq3d-shadow-xl); }
.eq3d-mhd { padding: 16px 20px; border-bottom: 1px solid var(--eq3d-border); display: flex; align-items: center; gap: 12px; }
.eq3d-mhd h4 { font-size: 15px; font-weight: 700; flex: 1; letter-spacing: -.2px; margin: 0; }
.eq3d-mcl { background: none; border: none; color: var(--eq3d-muted); font-size: 20px; cursor: pointer; line-height: 1; border-radius: 6px; padding: 2px 4px; transition: all .12s; }
.eq3d-mcl:hover { color: var(--eq3d-text); background: var(--eq3d-card); }
.eq3d-mbd { flex: 1; overflow-y: auto; padding: 16px; }
.eq3d-mft { padding: 14px 18px; border-top: 1px solid var(--eq3d-border); display: flex; align-items: center; gap: 10px; background: var(--eq3d-surface); }
.eq3d-ctbl { width: 100%; border-collapse: collapse; font-size: 12px; }
.eq3d-ctbl th { font-size: 10px; font-weight: 600; text-transform: uppercase; letter-spacing: .5px; color: var(--eq3d-muted); padding: 8px; border-bottom: 1px solid var(--eq3d-border); text-align: left; font-family: var(--eq3d-mono); }
.eq3d-ctbl td { padding: 10px 8px; border-bottom: 1px solid var(--eq3d-border); vertical-align: middle; }
.eq3d-ctbl tr:last-child td { border-bottom: none; }
.eq3d-ctbl tr:hover td { background: var(--eq3d-surface); }
.eq3d-rbtn { background: none; border: none; color: var(--eq3d-muted); cursor: pointer; font-size: 13px; padding: 4px 6px; border-radius: 6px; transition: all .12s; }
.eq3d-rbtn:hover { color: var(--eq3d-red); background: rgba(239,68,68,.08); }

/* ── Toasts ── */
.eq3d-toasts { position: fixed; bottom: 18px; right: 18px; z-index: 999; display: flex; flex-direction: column; gap: 6px; pointer-events: none; }
.eq3d-toast { background: var(--eq3d-panel); border: 1px solid var(--eq3d-border); border-left: 3px solid var(--eq3d-primary); border-radius: var(--eq3d-radius); padding: 10px 14px; font-size: 12px; color: var(--eq3d-text); font-weight: 500; animation: eq3d-tIn .25s ease; box-shadow: var(--eq3d-shadow-lg); }
@keyframes eq3d-tIn { from { opacity: 0; transform: translateX(14px); } to { opacity: 1; transform: none; } }
</style>
