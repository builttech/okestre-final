from pathlib import Path
from playwright.sync_api import sync_playwright, expect


def test_drag_ids_and_undo(tmp_path):
    static = Path(__file__).parents[1] / "gitide_server" / "static"
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True)
        page = browser.new_page(viewport={"width":1600,"height":1000})
        errors=[]
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.route("http://flow.test/**", lambda route: route.fulfill(
            content_type="application/json", body='{"files":[]}'))
        page.goto("http://flow.test/")
        page.set_content('<style>body{margin:0}#flowcharts-app{height:980px}</style><button data-tab="tab-flowcharts">Fluxogramas</button><div id="flowcharts-app"></div><script>window.state={activeProjectId:1};window.getHeaders=()=>({});</script>')
        page.add_style_tag(path=str(static / "flowcharts.css"))
        page.add_script_tag(path=str(static / "flowcharts.js"))
        nodes=page.locator(".react-flow__node")
        expect(nodes).to_have_count(3)
        expect(nodes.first).to_be_visible()
        page.wait_for_timeout(400)
        page.evaluate("""() => {
            window.hiddenFrames=0;window.watchDrag=true;
            function watch(){if(!window.watchDrag)return;
                for(const n of document.querySelectorAll('.react-flow__node')){
                    const s=getComputedStyle(n);if(s.visibility==='hidden'||s.opacity==='0')window.hiddenFrames++;
                }requestAnimationFrame(watch);
            }requestAnimationFrame(watch);
        }""")
        node=page.locator('.react-flow__node[data-id="n2"]')
        before=node.get_attribute("style")
        box=node.bounding_box()
        page.mouse.move(box['x']+90,box['y']+44)
        page.mouse.down()
        page.mouse.move(box['x']+210,box['y']+110,steps=40)
        page.mouse.up()
        page.evaluate("window.watchDrag=false")
        assert node.get_attribute("style") != before
        assert page.evaluate("window.hiddenFrames") == 0
        page.get_by_role("button",name="Código",exact=True).click()
        source=page.locator('#fc-code').input_value()
        assert 'n1 --> n2' in source and 'n2 --> n3' in source
        assert 'n_' not in source
        page.get_by_role("button",name="Fechar",exact=True).click()
        node.locator(".fc-node > span").click()
        page.get_by_role("button",name="Duplicar nó",exact=True).click()
        expect(page.locator('.react-flow__node[data-id="n4"]')).to_be_visible()
        page.get_by_role("button",name="Desfazer",exact=True).click()
        expect(nodes).to_have_count(3)
        assert not errors, errors
        browser.close()


def test_text_style_routing_clipboard_and_roundtrip(tmp_path):
    import json
    from urllib.parse import urlparse, parse_qs
    static=Path(__file__).parents[1]/'gitide_server/static'
    stored={}
    def respond(route):
        request=route.request
        url=urlparse(request.url)
        if url.path.endswith('/write'):
            body=request.post_data_json
            stored[body['filepath']]=body['content']
            route.fulfill(json={'ok':True})
        elif url.path.endswith('/read'):
            name=parse_qs(url.query)['filepath'][0]
            route.fulfill(status=200 if name in stored else 404,json={'content':stored.get(name,'')})
        else: route.fulfill(json={'files':[{'path':name} for name in stored]})
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True)
        page=browser.new_page(viewport={'width':1600,'height':1000},accept_downloads=True)
        errors=[]
        page.on('pageerror',lambda error:errors.append(str(error)))
        page.route('http://flow.test/**',respond)
        page.goto('http://flow.test/')
        page.set_content('<style>body{margin:0}#flowcharts-app{height:980px}</style><button data-tab="tab-flowcharts">Fluxogramas</button><div id="flowcharts-app"></div><script>window.state={activeProjectId:1};window.getHeaders=()=>({});</script>')
        page.add_style_tag(path=str(static/'flowcharts.css'))
        page.add_script_tag(path=str(static/'flowcharts.js'))
        node=page.locator('.react-flow__node[data-id="n2"]')
        expect(node).to_be_visible()
        expect(node.locator('.react-flow__handle')).to_have_count(4)
        node.locator('.fc-node > span').dblclick()
        page.get_by_label('Texto do nó',exact=True).fill('Cadastro da empresa')
        page.get_by_label('Texto do nó',exact=True).press('Enter')
        expect(node.locator('.fc-node > span')).to_have_text('Cadastro da empresa')
        node.locator('.fc-node > span').click()
        for label,value in [('Cor de fundo','#334455'),('Cor da borda','#aabbcc')]:
            page.get_by_label(label,exact=True).evaluate('(el,value)=>{Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,"value").set.call(el,value);el.dispatchEvent(new Event("input",{bubbles:true}));el.dispatchEvent(new Event("change",{bubbles:true}));}',value)
        expect(node.locator('.fc-node > svg')).to_have_css('fill','rgb(51, 68, 85)')
        page.locator('.fc-root').focus()
        page.keyboard.press('Control+c')
        page.keyboard.press('Control+v')
        expect(page.locator('.react-flow__node[data-id="n4"]')).to_be_visible()
        page.keyboard.press('Control+d')
        expect(page.locator('.react-flow__node[data-id="n5"]')).to_be_visible()
        # Connect explicit left/right ports, independent of the diagram direction.
        first=page.locator('.react-flow__node[data-id="n1"] .react-flow__handle[data-handleid="right"]')
        last=page.locator('.react-flow__node[data-id="n3"] .react-flow__handle[data-handleid="left"]')
        a,b=first.bounding_box(),last.bounding_box()
        page.mouse.move(a['x']+5,a['y']+5)
        page.mouse.down()
        page.mouse.move(b['x']+5,b['y']+5,steps=20)
        page.mouse.up()
        expect(page.locator('.react-flow__edge')).to_have_count(3)
        # Select an edge then edit its label on the canvas.
        page.locator('.react-flow__edge').first.dispatch_event('click')
        page.get_by_label('Caminho da conexão').select_option('straight')
        page.get_by_label('Caminho da conexão').select_option('default')
        page.get_by_label('Rótulo',exact=True).fill('Sim')
        label=page.get_by_role('button',name='Editar rótulo da conexão').filter(has_text='Sim')
        label.dblclick()
        page.get_by_label('Texto da conexão').fill('Não')
        page.get_by_label('Texto da conexão').press('Enter')
        page.locator('#fc-name').fill('teste-visual')
        page.locator('#fc-save').click()
        expect(page.locator('#fc-status')).to_have_text('Fluxograma salvo no projeto.')
        source=stored['.documents/fluxogramas/teste-visual.mmd']
        graph=json.loads(stored['.documents/fluxogramas/teste-visual.editor.json'])['graph']
        assert 'style n2 fill:#334455,stroke:#aabbcc' in source
        assert '|"Não"|' in source
        assert graph['edges'][-1]['sourceHandle']=='right'
        assert graph['edges'][-1]['targetHandle']=='left'
        assert graph['edges'][0]['data']['routing']=='default'
        page.get_by_role('button',name='Novo',exact=True).click()
        page.once('dialog',lambda dialog:dialog.accept())
        page.locator('#fc-files button').first.click()
        expect(page.locator('.react-flow__node')).to_have_count(5)
        expect(node.locator('.fc-node > svg')).to_have_css('fill','rgb(51, 68, 85)')
        # Reapply exported Mermaid without relying on its editor sidecar.
        page.add_script_tag(path=str(static/'vendor/mermaid-11.12.0.min.js'))
        page.get_by_role('button',name='Código',exact=True).click()
        page.get_by_role('button',name='Aplicar ao canvas',exact=True).click()
        expect(page.locator('#fc-code')).to_have_count(0)
        expect(node.locator('.fc-node > svg')).to_have_css('fill','rgb(51, 68, 85)')
        with page.expect_download() as download:
            page.locator('#fc-export-svg').click()
        svg=Path(download.value.path()).read_text(encoding='utf-8')
        assert '#334455' in svg and '#aabbcc' in svg
        assert not errors,errors
        page.screenshot(path=str(tmp_path/'flowchart.png'))
        browser.close()
