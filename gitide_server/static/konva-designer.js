(function () {
    "use strict";

    const STORAGE_KEY = "actia-konva-designer-v1";
    const STAGE_WIDTH = 2700;
    const STAGE_HEIGHT = 1500;
    const $ = (selector, root = document) => root.querySelector(selector);
    const $$ = (selector, root = document) => Array.from(root.querySelectorAll(selector));

    const state = {
        tool: "select",
        zoom: 0.53,
        selectedId: null,
        editingPageId: null,
        pageMenuPageId: null,
        dragSnapshot: null,
        doc: {
            name: "Novo arquivo 1",
            activePageId: "page-1",
            pages: [{ id: "page-1", name: "Page 1" }],
            nodes: []
        }
    };

    const stage = new Konva.Stage({
        container: "konva-stage",
        width: STAGE_WIDTH,
        height: STAGE_HEIGHT
    });
    const gridLayer = new Konva.Layer({ listening: false });
    const contentLayer = new Konva.Layer();
    const uiLayer = new Konva.Layer();
    const transformer = new Konva.Transformer({
        rotateEnabled: true,
        keepRatio: false,
        padding: 0,
        borderStroke: "#79f3e6",
        borderStrokeWidth: 1,
        anchorStroke: "#79f3e6",
        anchorFill: "#ffffff",
        anchorSize: 8,
        anchorCornerRadius: 8
    });
    const frameLabelsGroup = new Konva.Group({ listening: false });
    const frameDropHighlight = new Konva.Group({ listening: false, visible: false });
    const frameSelectionMeta = new Konva.Group({ listening: false });

    stage.add(gridLayer);
    stage.add(contentLayer);
    uiLayer.add(frameLabelsGroup);
    uiLayer.add(frameDropHighlight);
    uiLayer.add(transformer);
    uiLayer.add(frameSelectionMeta);
    stage.add(uiLayer);

    function uid(prefix) {
        return `${prefix}-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 7)}`;
    }

    function getActivePageId() {
        return state.doc.activePageId || state.doc.pages?.[0]?.id || "page-1";
    }

    function getActivePage() {
        return state.doc.pages?.find((page) => page.id === getActivePageId()) || state.doc.pages?.[0] || { id: "page-1", name: "Page 1" };
    }

    function getPageNodes(pageId = getActivePageId()) {
        return state.doc.nodes.filter((item) => (item.pageId || "page-1") === pageId);
    }

    function createDefaultNodesForPage(pageId, useLegacyIds = false) {
        const boardId = useLegacyIds ? "board" : `board-${pageId}`;
        return [
            {
                id: boardId,
                type: "frame",
                name: "Board",
                pageId,
                x: 420,
                y: 120,
                width: 1440,
                height: 1024,
                fill: "#ffffff",
                stroke: "transparent",
                strokeWidth: 0,
                cornerRadius: 0,
                opacity: 1,
                locked: false
            },
            {
                id: useLegacyIds ? "headline-01" : `headline-${pageId}`,
                type: "text",
                name: "01",
                pageId,
                x: 470,
                y: 170,
                width: 120,
                height: 36,
                text: "01",
                fill: "#000000",
                fontSize: 28,
                fontStyle: "normal",
                opacity: 1,
                parentId: boardId
            }
        ];
    }

    function getPointer() {
        const pointer = stage.getPointerPosition() || { x: 680, y: 280 };
        return {
            x: Math.round((pointer.x - stage.x()) / state.zoom),
            y: Math.round((pointer.y - stage.y()) / state.zoom)
        };
    }

    function defaultNodes() {
        return createDefaultNodesForPage("page-1", true);
    }

    function loadDoc() {
        try {
            const raw = localStorage.getItem(STORAGE_KEY);
            if (raw) {
                const parsed = JSON.parse(raw);
                if (parsed && Array.isArray(parsed.nodes)) {
                    state.doc = parsed;
                    normalizeDoc();
                    return;
                }
            }
        } catch (error) {
            console.warn("Konva designer storage reset:", error);
        }
        state.doc.nodes = defaultNodes();
        normalizeDoc();
        persistDoc();
    }

    function normalizeDoc() {
        if (!Array.isArray(state.doc.pages) || !state.doc.pages.length) {
            state.doc.pages = [{ id: "page-1", name: "Page 1" }];
        }
        state.doc.pages.forEach((page, index) => {
            page.id = page.id || uid("page");
            page.name = page.name || `Page ${index + 1}`;
        });
        if (!state.doc.activePageId || !state.doc.pages.some((page) => page.id === state.doc.activePageId)) {
            state.doc.activePageId = state.doc.pages[0].id;
        }
        if (!Array.isArray(state.doc.nodes)) state.doc.nodes = [];
        state.doc.nodes.forEach((item) => {
            if (!item.pageId) item.pageId = "page-1";
        });
        let board = state.doc.nodes.find((item) => item.id === "board" && item.type === "frame");
        if (!board) {
            state.doc.nodes.unshift(...defaultNodes());
            board = state.doc.nodes.find((item) => item.id === "board" && item.type === "frame");
        }
        const isLegacyDefault = Number(board.width) === 1024 && Number(board.height) === 768;
        if (isLegacyDefault) {
            board.x = 420;
            board.y = 120;
            board.width = 1440;
            board.height = 1024;
            board.fill = "#ffffff";
            board.stroke = "transparent";
            board.strokeWidth = 0;
            const headline = state.doc.nodes.find((item) => item.id === "headline-01");
            if (headline) {
                headline.x = board.x + 50;
                headline.y = board.y + 50;
            }
        }
        state.doc.nodes.forEach((item) => {
            if (item.type === "frame" && (item.id === "board" || item.id.startsWith("board-"))) {
                delete item.parentId;
                return;
            }
            if (!item.parentId) {
                item.parentId = findContainingFrameForData(item, item.id)?.id || null;
            }
        });
    }

    function persistDoc() {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(state.doc, null, 2));
        renderJsonPreview();
    }

    function drawGrid() {
        gridLayer.destroyChildren();
        const minor = 20;
        const major = 100;
        for (let x = 0; x <= STAGE_WIDTH; x += minor) {
            gridLayer.add(new Konva.Line({
                points: [x, 0, x, STAGE_HEIGHT],
                stroke: x % major === 0 ? "rgba(130,150,170,0.18)" : "rgba(130,150,170,0.08)",
                strokeWidth: 1
            }));
        }
        for (let y = 0; y <= STAGE_HEIGHT; y += minor) {
            gridLayer.add(new Konva.Line({
                points: [0, y, STAGE_WIDTH, y],
                stroke: y % major === 0 ? "rgba(130,150,170,0.18)" : "rgba(130,150,170,0.08)",
                strokeWidth: 1
            }));
        }
        gridLayer.draw();
    }

    function createKonvaNode(data) {
        const common = {
            id: data.id,
            x: data.x || 0,
            y: data.y || 0,
            rotation: data.rotation || 0,
            opacity: data.opacity ?? 1,
            draggable: !data.locked
        };
        let node;
        if (data.type === "ellipse") {
            node = new Konva.Ellipse({
                ...common,
                radiusX: (data.width || 120) / 2,
                radiusY: (data.height || 120) / 2,
                fill: data.fill || "#ffffff",
                stroke: data.stroke || "#8ea0b8",
                strokeWidth: data.strokeWidth || 1
            });
        } else if (data.type === "text" || data.type === "heading" || data.type === "icon") {
            node = new Konva.Text({
                ...common,
                width: data.width || 180,
                text: data.text || (data.type === "icon" ? "Icon" : "Texto"),
                fill: data.fill || "#0f172a",
                fontSize: data.fontSize || (data.type === "heading" ? 32 : 18),
                fontFamily: data.fontFamily || "Inter",
                fontStyle: data.fontStyle || "normal",
                lineHeight: data.lineHeight || 1.2,
                padding: 0
            });
        } else if (data.type === "line") {
            node = new Konva.Line({
                ...common,
                points: data.points || [0, 0, data.width || 180, 0],
                stroke: data.stroke || "#0f172a",
                strokeWidth: data.strokeWidth || 2,
                lineCap: "round",
                lineJoin: "round"
            });
        } else {
            node = new Konva.Rect({
                ...common,
                width: data.width || 220,
                height: data.height || 140,
                fill: data.fill || (data.type === "frame" ? "#ffffff" : "#f8fafc"),
                stroke: data.stroke || "rgba(15,23,42,0.16)",
                strokeWidth: data.strokeWidth ?? (data.type === "frame" ? 0 : 1),
                cornerRadius: data.cornerRadius || 0
            });
        }
        node.setAttr("nodeType", data.type);
        node.setAttr("nodeName", data.name);
        wireNode(node);
        return node;
    }

    function nodeLabel(data) {
        if (data.type === "frame") return "Frame";
        if (data.type === "rect") return "Retângulo";
        if (data.type === "ellipse") return "Elipse";
        if (data.type === "line") return "Linha";
        if (data.type === "icon") return "Ícone";
        if (data.type === "heading") return "Heading";
        return "Texto";
    }

    function addNode(type) {
        const point = getPointer();
        const specs = {
            frame: { width: 1440, height: 1024, fill: "#ffffff", stroke: "transparent", strokeWidth: 0 },
            rect: { width: 220, height: 120, fill: "#f8fafc", stroke: "rgba(15,23,42,0.24)", cornerRadius: 8 },
            ellipse: { width: 160, height: 160, fill: "#f8fafc", stroke: "rgba(15,23,42,0.24)" },
            text: { width: 240, text: "Texto", fill: "#0f172a", fontSize: 18 },
            heading: { width: 420, text: "Título", fill: "#0f172a", fontSize: 34, fontStyle: "bold" },
            icon: { width: 140, text: "Icon", fill: "#0f172a", fontSize: 20, fontStyle: "bold" },
            image: { width: 220, height: 140, fill: "#e2e8f0", stroke: "rgba(15,23,42,0.24)", cornerRadius: 8 },
            line: { width: 220, stroke: "#0f172a", points: [0, 0, 220, 0] }
        };
        const id = uid(type);
        const base = specs[type] || specs.rect;
        const data = {
            id,
            type,
            name: type === "image" ? "Imagem" : nodeLabel({ type }),
            pageId: getActivePageId(),
            x: point.x,
            y: point.y,
            opacity: 1,
            ...base
        };
        if (type === "image") {
            data.type = "rect";
            data.name = "Imagem placeholder";
        }
        data.parentId = type === "frame"
            ? findContainingFrameAtPoint(point, null)?.id || null
            : getInsertionParent(point)?.id || null;
        state.doc.nodes.push(data);
        const node = createKonvaNode(data);
        contentLayer.add(node);
        selectNode(node);
        persistDoc();
        renderLayers();
        renderJsonPreview();
        setTool("select");
    }

    function wireNode(node) {
        node.on("click tap", (event) => {
            event.cancelBubble = true;
            if (state.tool !== "select") {
                addNode(state.tool);
                return;
            }
            selectNode(node);
        });
        node.on("dragstart", () => {
            const data = state.doc.nodes.find((item) => item.id === node.id());
            if (data?.type === "frame") claimContainedNodes(node.id());
            state.dragSnapshot = {
                id: node.id(),
                type: data?.type || node.getAttr("nodeType"),
                lastX: node.x(),
                lastY: node.y()
            };
        });
        node.on("dragmove", () => {
            const data = state.doc.nodes.find((item) => item.id === node.id());
            if (data?.type === "frame" && state.dragSnapshot?.id === node.id()) {
                const dx = node.x() - state.dragSnapshot.lastX;
                const dy = node.y() - state.dragSnapshot.lastY;
                if (dx || dy) {
                    moveFrameChildren(node.id(), dx, dy);
                    state.dragSnapshot.lastX = node.x();
                    state.dragSnapshot.lastY = node.y();
                }
            }
            renderFrameDropHighlight(findDropTargetForNode(node));
            renderFrameLabels();
            renderFrameSelectionMeta();
        });
        node.on("transform", () => {
            renderFrameLabels();
            renderFrameSelectionMeta();
        });
        node.on("dragend transformend", () => {
            syncNodeData(node);
            updateNodeParent(node);
            clearFrameDropHighlight();
            state.dragSnapshot = null;
            persistDoc();
            renderLayers();
            renderFrameLabels();
            renderFrameSelectionMeta();
            renderInspector();
        });
        node.on("dblclick dbltap", () => {
            if (node.className === "Text") {
                const next = window.prompt("Editar texto", node.text());
                if (next !== null) {
                    node.text(next);
                    syncNodeData(node);
                    persistDoc();
                    renderLayers();
                    renderInspector();
                }
            }
        });
    }

    function syncNodeData(node) {
        const data = state.doc.nodes.find((item) => item.id === node.id());
        if (!data) return;
        data.x = Math.round(node.x());
        data.y = Math.round(node.y());
        data.rotation = Math.round(node.rotation() || 0);
        data.opacity = Number((node.opacity() ?? 1).toFixed(2));
        if (node.className === "Ellipse") {
            data.width = Math.round(node.radiusX() * 2 * node.scaleX());
            data.height = Math.round(node.radiusY() * 2 * node.scaleY());
            node.radiusX(data.width / 2);
            node.radiusY(data.height / 2);
            node.scale({ x: 1, y: 1 });
            data.fill = node.fill();
            data.stroke = node.stroke();
        } else if (node.className === "Text") {
            data.width = Math.round(node.width() * node.scaleX());
            data.fontSize = Math.max(8, Math.round(node.fontSize() * node.scaleY()));
            node.width(data.width);
            node.fontSize(data.fontSize);
            node.scale({ x: 1, y: 1 });
            data.text = node.text();
            data.fill = node.fill();
            data.fontStyle = node.fontStyle();
            data.height = Math.round(node.height());
        } else if (node.className === "Line") {
            data.points = node.points();
            data.width = Math.abs(data.points[2] || 0);
            data.stroke = node.stroke();
            data.strokeWidth = node.strokeWidth();
        } else {
            data.width = Math.round(node.width() * node.scaleX());
            data.height = Math.round(node.height() * node.scaleY());
            node.width(data.width);
            node.height(data.height);
            node.scale({ x: 1, y: 1 });
            data.fill = node.fill();
            data.stroke = node.stroke();
            data.cornerRadius = node.cornerRadius();
        }
    }

    function nodeCenter(data) {
        return {
            x: (data.x || 0) + ((data.width || 0) / 2),
            y: (data.y || 0) + ((data.height || 0) / 2)
        };
    }

    function isPointInsideFrame(point, frame) {
        return point.x >= frame.x
            && point.x <= frame.x + (frame.width || 0)
            && point.y >= frame.y
            && point.y <= frame.y + (frame.height || 0);
    }

    function frameDepth(frame) {
        let depth = 0;
        let parentId = frame.parentId;
        while (parentId) {
            const parent = state.doc.nodes.find((item) => item.id === parentId);
            if (!parent) break;
            depth += 1;
            parentId = parent.parentId;
        }
        return depth;
    }

    function isDescendantOf(candidateId, ancestorId) {
        if (!candidateId || !ancestorId) return false;
        let parentId = state.doc.nodes.find((item) => item.id === candidateId)?.parentId;
        while (parentId) {
            if (parentId === ancestorId) return true;
            parentId = state.doc.nodes.find((item) => item.id === parentId)?.parentId;
        }
        return false;
    }

    function getDescendantIds(parentId) {
        const ids = new Set();
        let changed = true;
        while (changed) {
            changed = false;
            state.doc.nodes.forEach((item) => {
                if (item.parentId && (item.parentId === parentId || ids.has(item.parentId)) && !ids.has(item.id)) {
                    ids.add(item.id);
                    changed = true;
                }
            });
        }
        return ids;
    }

    function findContainingFrameAtPoint(point, excludeId, pageId = getActivePageId()) {
        return getPageNodes(pageId)
            .filter((item) => item.type === "frame"
                && item.id !== excludeId
                && !isDescendantOf(item.id, excludeId)
                && isPointInsideFrame(point, item))
            .sort((a, b) => {
                const areaA = (a.width || 0) * (a.height || 0);
                const areaB = (b.width || 0) * (b.height || 0);
                return areaA - areaB || frameDepth(b) - frameDepth(a);
            })[0] || null;
    }

    function findContainingFrameForData(data, excludeId) {
        return findContainingFrameAtPoint(nodeCenter(data), excludeId, data.pageId || getActivePageId());
    }

    function getInsertionParent(point) {
        const selected = state.doc.nodes.find((item) => item.id === state.selectedId);
        if (selected?.type === "frame" && isPointInsideFrame(point, selected)) return selected;
        return findContainingFrameAtPoint(point, null);
    }

    function findDropTargetForNode(node) {
        const box = nodeBox(node);
        const point = {
            x: box.x + (box.width / 2),
            y: box.y + (box.height / 2)
        };
        return findContainingFrameAtPoint(point, node.id());
    }

    function claimContainedNodes(frameId) {
        getPageNodes().forEach((item) => {
            if (item.id === frameId || item.id === "board" || item.id.startsWith("board-") || isDescendantOf(frameId, item.id)) return;
            const target = findContainingFrameForData(item, item.id);
            if (target?.id === frameId) item.parentId = frameId;
        });
    }

    function moveFrameChildren(frameId, dx, dy) {
        getDescendantIds(frameId).forEach((id) => {
            const child = contentLayer.findOne(`#${id}`);
            if (!child) return;
            child.position({
                x: child.x() + dx,
                y: child.y() + dy
            });
            syncNodeData(child);
        });
        contentLayer.batchDraw();
    }

    function renderFrameDropHighlight(frame) {
        frameDropHighlight.destroyChildren();
        if (!frame) {
            frameDropHighlight.visible(false);
            uiLayer.batchDraw();
            return;
        }
        const node = contentLayer.findOne(`#${frame.id}`);
        const box = node ? nodeBox(node) : frame;
        frameDropHighlight.add(new Konva.Rect({
            x: box.x,
            y: box.y,
            width: Math.max(1, box.width || 0),
            height: Math.max(1, box.height || 0),
            fill: "rgba(0, 212, 199, 0.08)",
            stroke: "#00d4c7",
            strokeWidth: 2,
            dash: [10, 6],
            listening: false
        }));
        frameDropHighlight.add(new Konva.Text({
            x: box.x + 10,
            y: box.y - 24,
            text: "Anexar ao frame",
            fontSize: 12,
            fontFamily: "Inter",
            fontStyle: "700",
            fill: "#00d4c7",
            listening: false
        }));
        frameDropHighlight.visible(true);
        uiLayer.batchDraw();
    }

    function clearFrameDropHighlight() {
        frameDropHighlight.destroyChildren();
        frameDropHighlight.visible(false);
        uiLayer.batchDraw();
    }

    function updateNodeParent(node) {
        const data = state.doc.nodes.find((item) => item.id === node.id());
        if (!data || data.id === "board" || data.id.startsWith("board-")) return;
        data.parentId = findContainingFrameForData(data, data.id)?.id || null;
    }

    function getSelectedNode() {
        return state.selectedId ? contentLayer.findOne(`#${state.selectedId}`) : null;
    }

    function nodeBox(node) {
        const type = node.getAttr("nodeType");
        if (type === "frame" || node.className === "Rect") {
            return {
                x: node.x(),
                y: node.y(),
                width: Math.round(node.width() * node.scaleX()),
                height: Math.round(node.height() * node.scaleY())
            };
        }
        const box = node.getClientRect({ relativeTo: contentLayer, skipShadow: true });
        return {
            x: box.x,
            y: box.y,
            width: Math.round(box.width),
            height: Math.round(box.height)
        };
    }

    function configureTransformer(node) {
        const isFrame = node?.getAttr("nodeType") === "frame";
        transformer.rotateEnabled(!isFrame);
        transformer.padding(isFrame ? 0 : 4);
        transformer.borderStroke(isFrame ? "#00d4c7" : "#79f3e6");
        transformer.borderStrokeWidth(1);
        transformer.anchorStroke(isFrame ? "#00d4c7" : "#79f3e6");
        transformer.anchorFill(isFrame ? "#ffffff" : "#111418");
        transformer.anchorSize(isFrame ? 8 : 9);
        transformer.anchorCornerRadius(isFrame ? 8 : 2);
        transformer.enabledAnchors(isFrame
            ? ["top-left", "top-right", "bottom-left", "bottom-right"]
            : ["top-left", "top-center", "top-right", "middle-left", "middle-right", "bottom-left", "bottom-center", "bottom-right"]);
    }

    function renderFrameLabels() {
        frameLabelsGroup.destroyChildren();
        getPageNodes()
            .filter((item) => item.type === "frame")
            .forEach((item) => {
                const node = contentLayer.findOne(`#${item.id}`);
                const x = node ? node.x() : item.x;
                const y = node ? node.y() : item.y;
                const selected = item.id === state.selectedId;
                frameLabelsGroup.add(new Konva.Text({
                    x,
                    y: (y || 0) - 22,
                    text: item.name || "Frame",
                    fontSize: 13,
                    fontFamily: "Inter",
                    fill: selected ? "#00d4c7" : "#8a99a8"
                }));
            });
    }

    function renderFrameSelectionMeta() {
        frameSelectionMeta.destroyChildren();
        const node = getSelectedNode();
        if (!node || node.getAttr("nodeType") !== "frame") {
            frameSelectionMeta.visible(false);
            uiLayer.batchDraw();
            return;
        }
        const box = nodeBox(node);
        const label = `${Math.max(1, box.width)} x ${Math.max(1, box.height)}`;
        const badgeText = new Konva.Text({
            x: 0,
            y: 0,
            text: label,
            fontSize: 12,
            fontFamily: "Inter",
            fontStyle: "700",
            fill: "#ffffff",
            padding: 0
        });
        const badgeWidth = badgeText.width() + 14;
        const badgeHeight = 18;
        const badgeX = box.x + (box.width / 2) - (badgeWidth / 2);
        const badgeY = box.y + box.height + 10;
        frameSelectionMeta.add(new Konva.Rect({
            x: badgeX,
            y: badgeY,
            width: badgeWidth,
            height: badgeHeight,
            fill: "#00d4c7",
            cornerRadius: 2
        }));
        badgeText.position({
            x: badgeX + 7,
            y: badgeY + 3
        });
        frameSelectionMeta.add(badgeText);
        frameSelectionMeta.visible(true);
        uiLayer.batchDraw();
    }

    function selectNode(node) {
        state.selectedId = node ? node.id() : null;
        configureTransformer(node);
        transformer.nodes(node ? [node] : []);
        transformer.forceUpdate();
        renderFrameLabels();
        renderFrameSelectionMeta();
        uiLayer.batchDraw();
        renderLayers();
        renderInspector();
    }

    function closePageMenu() {
        state.pageMenuPageId = null;
        const menu = $("#konva-page-menu");
        if (!menu) return;
        menu.hidden = true;
        menu.innerHTML = "";
    }

    function navigatePage(pageId) {
        if (!state.doc.pages.some((page) => page.id === pageId)) return;
        state.doc.activePageId = pageId;
        state.editingPageId = null;
        state.selectedId = null;
        closePageMenu();
        transformer.nodes([]);
        persistDoc();
        renderCanvas();
    }

    function startRenamePage(pageId) {
        if (!state.doc.pages.some((page) => page.id === pageId)) return;
        state.doc.activePageId = pageId;
        state.editingPageId = pageId;
        closePageMenu();
        renderCanvas();
        requestAnimationFrame(() => {
            const input = $(`.konva-page-name-input[data-page-id="${pageId}"]`);
            input?.focus();
            input?.select();
        });
    }

    function commitRenamePage(pageId, value) {
        const page = state.doc.pages.find((item) => item.id === pageId);
        if (!page) return;
        const nextName = String(value || "").trim();
        if (nextName) page.name = nextName;
        state.editingPageId = null;
        persistDoc();
        renderPageList();
    }

    function cancelRenamePage() {
        state.editingPageId = null;
        renderPageList();
    }

    function addPage() {
        const pageId = uid("page");
        const page = { id: pageId, name: `Page ${state.doc.pages.length + 1}` };
        state.doc.pages.push(page);
        state.doc.nodes.push(...createDefaultNodesForPage(pageId));
        navigatePage(pageId);
        startRenamePage(pageId);
    }

    function duplicatePage(pageId) {
        const source = state.doc.pages.find((page) => page.id === pageId);
        if (!source) return;
        const nextPageId = uid("page");
        const idMap = new Map();
        const sourceNodes = getPageNodes(pageId);
        sourceNodes.forEach((item) => {
            idMap.set(item.id, item.type === "frame" && (item.id === "board" || item.id.startsWith("board-")) ? `board-${nextPageId}` : uid(item.type || "node"));
        });
        const clonedNodes = sourceNodes.map((item) => ({
            ...JSON.parse(JSON.stringify(item)),
            id: idMap.get(item.id),
            pageId: nextPageId,
            parentId: item.parentId ? idMap.get(item.parentId) || null : null
        }));
        state.doc.pages.push({ id: nextPageId, name: `${source.name || "Page"} copy` });
        state.doc.nodes.push(...clonedNodes);
        navigatePage(nextPageId);
    }

    function deletePage(pageId) {
        if (state.doc.pages.length <= 1) return;
        const page = state.doc.pages.find((item) => item.id === pageId);
        if (!page) return;
        const confirmed = window.confirm(`Excluir "${page.name}" e todos os layers desta página?`);
        if (!confirmed) return;
        state.doc.pages = state.doc.pages.filter((item) => item.id !== pageId);
        state.doc.nodes = state.doc.nodes.filter((item) => (item.pageId || "page-1") !== pageId);
        if (state.doc.activePageId === pageId) state.doc.activePageId = state.doc.pages[0]?.id || "page-1";
        state.editingPageId = null;
        closePageMenu();
        selectNode(null);
        persistDoc();
        renderCanvas();
    }

    function openPageMenu(pageId, row) {
        const menu = $("#konva-page-menu");
        if (!menu) return;
        const page = state.doc.pages.find((item) => item.id === pageId);
        if (!page) return;
        state.pageMenuPageId = pageId;
        menu.innerHTML = `
            <button type="button" data-page-action="open"><i data-lucide="arrow-right"></i><span>Abrir página</span></button>
            <button type="button" data-page-action="rename"><i data-lucide="pencil"></i><span>Renomear</span></button>
            <button type="button" data-page-action="duplicate"><i data-lucide="copy"></i><span>Duplicar</span></button>
            <button type="button" data-page-action="delete" class="is-danger"><i data-lucide="trash-2"></i><span>Excluir</span></button>
        `;
        const rowBox = row.getBoundingClientRect();
        const paneBox = row.closest(".konva-left-pane").getBoundingClientRect();
        menu.style.top = `${rowBox.bottom - paneBox.top + 6}px`;
        menu.style.left = `${Math.min(16, Math.max(12, rowBox.left - paneBox.left))}px`;
        menu.hidden = false;
        $$("[data-page-action]", menu).forEach((button) => {
            button.addEventListener("click", (event) => {
                event.stopPropagation();
                const action = button.dataset.pageAction;
                if (action === "open") navigatePage(pageId);
                if (action === "rename") startRenamePage(pageId);
                if (action === "duplicate") duplicatePage(pageId);
                if (action === "delete") deletePage(pageId);
            });
        });
        refreshIcons();
    }

    function renderPageList(props = {}) {
        const list = $("#konva-page-list");
        if (!list) return;
        const options = {
            pages: state.doc.pages,
            activePageId: getActivePageId(),
            editingPageId: state.editingPageId,
            onNavigate: navigatePage,
            onMenu: openPageMenu,
            onRenameStart: startRenamePage,
            onRenameCommit: commitRenamePage,
            onRenameCancel: cancelRenamePage,
            onDelete: deletePage,
            ...props
        };
        const activePage = options.pages.find((page) => page.id === options.activePageId) || options.pages[0];
        const title = $("#konva-active-page-title");
        if (title) title.textContent = activePage?.name || "Page";
        list.innerHTML = options.pages.map((page) => {
            const active = page.id === options.activePageId ? " is-active" : "";
            const editing = page.id === options.editingPageId ? " is-renaming" : "";
            if (editing) {
                return `<div class="konva-page-item${active}${editing}" data-page-id="${page.id}">
                    <i data-lucide="file"></i>
                    <input class="konva-page-name-input" data-page-id="${page.id}" value="${escapeHtml(page.name)}" aria-label="Renomear página">
                </div>`;
            }
            return `<div class="konva-page-item${active}" data-page-id="${page.id}" tabindex="0" role="button" aria-label="Página ${escapeHtml(page.name)}">
                <span class="konva-page-label"><i data-lucide="file"></i><span>${escapeHtml(page.name)}</span></span>
                <button class="konva-page-delete" type="button" title="Excluir página" aria-label="Excluir ${escapeHtml(page.name)}">
                    <i data-lucide="trash-2"></i>
                </button>
            </div>`;
        }).join("");
        $$(".konva-page-item", list).forEach((row) => {
            const pageId = row.dataset.pageId;
            let clickTimer = null;
            row.addEventListener("contextmenu", (event) => {
                event.preventDefault();
                options.onNavigate(pageId);
            });
            row.addEventListener("click", (event) => {
                if (event.target.closest(".konva-page-delete, input")) return;
                window.clearTimeout(clickTimer);
                clickTimer = window.setTimeout(() => options.onMenu(pageId, row), 180);
            });
            row.addEventListener("dblclick", (event) => {
                event.preventDefault();
                window.clearTimeout(clickTimer);
                options.onNavigate(pageId);
                options.onRenameStart(pageId);
            });
            row.addEventListener("keydown", (event) => {
                if (event.key === "Enter") options.onMenu(pageId, row);
            });
        });
        $$(".konva-page-delete", list).forEach((button) => {
            button.addEventListener("click", (event) => {
                event.stopPropagation();
                options.onDelete(button.closest(".konva-page-item")?.dataset.pageId);
            });
        });
        $$(".konva-page-name-input", list).forEach((input) => {
            input.addEventListener("keydown", (event) => {
                if (event.key === "Enter") options.onRenameCommit(input.dataset.pageId, input.value);
                if (event.key === "Escape") options.onRenameCancel();
            });
            input.addEventListener("blur", () => options.onRenameCommit(input.dataset.pageId, input.value));
        });
        refreshIcons();
    }

    function renderCanvas() {
        contentLayer.destroyChildren();
        getPageNodes().forEach((data) => contentLayer.add(createKonvaNode(data)));
        contentLayer.draw();
        renderPageList();
        renderFrameLabels();
        renderFrameSelectionMeta();
        renderLayers();
        renderInspector();
        renderJsonPreview();
    }

    function renderLayers() {
        const tree = $("#konva-layer-tree");
        if (!tree) return;
        const pageNodes = getPageNodes();
        const nodeMap = new Map(pageNodes.map((item) => [item.id, { ...item, children: [] }]));
        const roots = [];
        pageNodes.forEach((item) => {
            const node = nodeMap.get(item.id);
            const parent = item.parentId ? nodeMap.get(item.parentId) : null;
            if (parent && parent.id !== node.id) parent.children.push(node);
            else roots.push(node);
        });
        const rows = [];
        const walk = (items, depth = 0) => {
            [...items].reverse().forEach((item) => {
                rows.push({ item, depth });
                if (item.children?.length) walk(item.children, depth + 1);
            });
        };
        walk(roots, 0);
        tree.innerHTML = rows.map(({ item, depth }) => {
            const active = item.id === state.selectedId ? " is-active" : "";
            const icon = item.type === "frame" ? "scan" : item.type === "text" ? "type" : item.type === "ellipse" ? "circle" : item.type === "line" ? "pen-line" : "square";
            const boundedDepth = Math.min(depth, 6);
            return `<button class="konva-layer-row${active}" type="button" data-depth="${boundedDepth}" data-node-id="${item.id}">
                <i data-lucide="${icon}"></i>
                <span>${escapeHtml(item.name || nodeLabel(item))}</span>
            </button>`;
        }).join("");
        $$(".konva-layer-row", tree).forEach((button) => {
            button.addEventListener("click", () => {
                const node = contentLayer.findOne(`#${button.dataset.nodeId}`);
                selectNode(node);
            });
        });
        refreshIcons();
    }

    function renderInspector() {
        const empty = $("#konva-inspector-empty");
        const form = $("#konva-inspector");
        const node = getSelectedNode();
        if (!empty || !form) return;
        empty.hidden = Boolean(node);
        form.hidden = !node;
        if (!node) return;
        syncNodeData(node);
        const data = state.doc.nodes.find((item) => item.id === node.id());
        $("#konva-selected-type").textContent = nodeLabel(data || { type: "layer" });
        $("#konva-selected-name").textContent = data?.name || node.id();
        setProp("x", data.x);
        setProp("y", data.y);
        setProp("width", data.width || Math.round(node.width()));
        setProp("height", data.height || Math.round(node.height()));
        setProp("fill", data.fill || node.fill?.() || "");
        setProp("stroke", data.stroke || node.stroke?.() || "");
        setProp("cornerRadius", data.cornerRadius || 0);
        setProp("opacity", data.opacity ?? 1);
        setProp("text", data.text || "");
        setProp("fontSize", data.fontSize || "");
        setProp("fontStyle", data.fontStyle || "normal");
        $$(".konva-text-prop, [data-prop='fontSize'], [data-prop='fontStyle']").forEach((field) => {
            field.closest("label")?.toggleAttribute("hidden", node.className !== "Text");
        });
    }

    function setProp(prop, value) {
        const field = $(`[data-prop="${prop}"]`);
        if (field) field.value = value ?? "";
    }

    function updateSelectedFromInspector(event) {
        const field = event.target.closest("[data-prop]");
        if (!field) return;
        const node = getSelectedNode();
        if (!node) return;
        const prop = field.dataset.prop;
        const numeric = ["x", "y", "width", "height", "cornerRadius", "opacity", "fontSize"].includes(prop);
        const value = numeric ? Number(field.value) : field.value;
        if (prop === "width") {
            if (node.className === "Ellipse") node.radiusX(Math.max(2, value) / 2);
            else if (node.className === "Text") node.width(Math.max(20, value));
            else if (node.className !== "Line") node.width(Math.max(2, value));
        } else if (prop === "height") {
            if (node.className === "Ellipse") node.radiusY(Math.max(2, value) / 2);
            else if (node.className !== "Line" && node.className !== "Text") node.height(Math.max(2, value));
        } else if (prop === "cornerRadius" && node.cornerRadius) {
            node.cornerRadius(Math.max(0, value));
        } else if (prop === "text" && node.className === "Text") {
            node.text(value);
        } else if (prop === "fontSize" && node.className === "Text") {
            node.fontSize(Math.max(8, value));
        } else if (prop === "fontStyle" && node.className === "Text") {
            node.fontStyle(value);
        } else if (prop === "fill" && node.fill) {
            node.fill(value);
        } else if (prop === "stroke" && node.stroke) {
            node.stroke(value);
        } else if (prop === "opacity") {
            node.opacity(Math.min(1, Math.max(0, value)));
        } else if (prop === "x" || prop === "y") {
            node[prop](value);
        }
        syncNodeData(node);
        persistDoc();
        contentLayer.batchDraw();
        renderFrameLabels();
        renderFrameSelectionMeta();
        uiLayer.batchDraw();
        renderLayers();
    }

    function setTool(tool) {
        state.tool = tool;
        $$("[data-tool]").forEach((button) => button.classList.toggle("is-active", button.dataset.tool === tool));
        stage.container().style.cursor = tool === "select" ? "default" : "crosshair";
    }

    function deleteSelected() {
        const node = getSelectedNode();
        if (!node || node.id() === "board" || node.id().startsWith("board-")) return;
        const idsToDelete = new Set([node.id()]);
        let changed = true;
        while (changed) {
            changed = false;
            state.doc.nodes.forEach((item) => {
                if (item.parentId && idsToDelete.has(item.parentId) && !idsToDelete.has(item.id)) {
                    idsToDelete.add(item.id);
                    changed = true;
                }
            });
        }
        state.doc.nodes = state.doc.nodes.filter((item) => !idsToDelete.has(item.id));
        state.doc.nodes.forEach((item) => {
            if (item.parentId && idsToDelete.has(item.parentId)) item.parentId = null;
        });
        idsToDelete.forEach((id) => contentLayer.findOne(`#${id}`)?.destroy());
        selectNode(null);
        persistDoc();
        contentLayer.draw();
    }

    function duplicateSelected() {
        const data = state.doc.nodes.find((item) => item.id === state.selectedId);
        if (!data) return;
        const clone = {
            ...JSON.parse(JSON.stringify(data)),
            id: uid(data.type),
            name: `${data.name || nodeLabel(data)} copy`,
            pageId: data.pageId || getActivePageId(),
            x: (data.x || 0) + 32,
            y: (data.y || 0) + 32
        };
        clone.parentId = data.parentId || null;
        state.doc.nodes.push(clone);
        const node = createKonvaNode(clone);
        contentLayer.add(node);
        selectNode(node);
        persistDoc();
        renderLayers();
    }

    function applyZoom(nextZoom) {
        state.zoom = Math.min(1.6, Math.max(0.25, Number(nextZoom.toFixed(2))));
        stage.scale({ x: state.zoom, y: state.zoom });
        stage.batchDraw();
        const label = `${Math.round(state.zoom * 100)}%`;
        $("#konva-zoom-label").textContent = label;
        $("#konva-right-zoom").textContent = label;
    }

    function renderRulers() {
        const top = $("#konva-ruler-top");
        const left = $("#konva-ruler-left");
        if (top) {
            top.innerHTML = "";
            for (let x = 300; x <= 2600; x += 100) {
                const mark = document.createElement("span");
                mark.textContent = String(x);
                mark.style.left = `${x * state.zoom}px`;
                top.appendChild(mark);
            }
        }
        if (left) {
            left.innerHTML = "";
            for (let y = -200; y <= 1400; y += 100) {
                const mark = document.createElement("span");
                mark.textContent = String(y);
                mark.style.top = `${(y + 220) * state.zoom}px`;
                left.appendChild(mark);
            }
        }
    }

    function renderJsonPreview() {
        const target = $("#konva-json-preview");
        if (target) target.textContent = JSON.stringify(state.doc, null, 2);
    }

    function exportJson() {
        const blob = new Blob([JSON.stringify(state.doc, null, 2)], { type: "application/json" });
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = url;
        link.download = "act-ia-design-canvas.json";
        link.click();
        URL.revokeObjectURL(url);
    }

    function escapeHtml(value) {
        return String(value || "")
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;");
    }

    function refreshIcons() {
        if (window.lucide) window.lucide.createIcons();
    }

    function bindUi() {
        $$("[data-tool]").forEach((button) => button.addEventListener("click", () => setTool(button.dataset.tool)));
        $$("[data-left-tab]").forEach((button) => {
            button.addEventListener("click", () => {
                $$("[data-left-tab]").forEach((item) => item.classList.toggle("is-active", item === button));
                $$("[data-left-pane]").forEach((pane) => pane.classList.toggle("is-active", pane.dataset.leftPane === button.dataset.leftTab));
            });
        });
        $$("[data-right-tab]").forEach((button) => {
            button.addEventListener("click", () => {
                $$("[data-right-tab]").forEach((item) => item.classList.toggle("is-active", item === button));
                $$("[data-right-pane]").forEach((pane) => pane.classList.toggle("is-active", pane.dataset.rightPane === button.dataset.rightTab));
                renderJsonPreview();
            });
        });
        $("#konva-inspector")?.addEventListener("input", updateSelectedFromInspector);
        $("#konva-delete")?.addEventListener("click", deleteSelected);
        $("#konva-duplicate")?.addEventListener("click", duplicateSelected);
        $("#konva-add-page")?.addEventListener("click", addPage);
        $("#konva-save")?.addEventListener("click", () => {
            persistDoc();
            $("#konva-save").classList.add("is-saved");
            setTimeout(() => $("#konva-save")?.classList.remove("is-saved"), 900);
        });
        $("#konva-export-json")?.addEventListener("click", exportJson);
        $("#konva-zoom-in")?.addEventListener("click", () => applyZoom(state.zoom + 0.1));
        $("#konva-zoom-out")?.addEventListener("click", () => applyZoom(state.zoom - 0.1));
        stage.on("click tap", (event) => {
            if (state.tool !== "select") {
                addNode(state.tool);
                return;
            }
            if (event.target === stage) selectNode(null);
        });
        window.addEventListener("keydown", (event) => {
            if (event.target.matches("input, textarea, select")) return;
            if (event.key === "Delete" || event.key === "Backspace") deleteSelected();
            if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "d") {
                event.preventDefault();
                duplicateSelected();
            }
            if (event.key === "v") setTool("select");
            if (event.key === "f") setTool("frame");
            if (event.key === "r") setTool("rect");
            if (event.key === "t") setTool("text");
        });
        document.addEventListener("click", (event) => {
            if (event.target.closest("#konva-page-menu, .konva-page-item")) return;
            closePageMenu();
        });
    }

    loadDoc();
    drawGrid();
    renderCanvas();
    renderRulers();
    bindUi();
    applyZoom(state.zoom);
    refreshIcons();
})();
