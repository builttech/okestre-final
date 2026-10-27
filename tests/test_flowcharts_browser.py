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
