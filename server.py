import sqlite3, json, os, time, requests
from flask import Flask, request, jsonify, send_file, send_from_directory
from datetime import datetime

app = Flask(__name__, static_folder='static', static_url_path='')
DB = os.path.expanduser('~/.oh-my-config/db')

def init():
    os.makedirs(os.path.dirname(DB), exist_ok=True)
    conn = sqlite3.connect(DB)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS project (
            id INTEGER PRIMARY KEY,
            name TEXT UNIQUE,
            description TEXT
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS config (
            id INTEGER PRIMARY KEY,
            project TEXT,
            type TEXT,
            name TEXT,
            content TEXT,
            version INT DEFAULT 1,
            updated_at TEXT,
            UNIQUE(project, type, name)
        )
    ''')
    conn.commit()
    conn.close()
init()

HELP_README = """# oh-my-config 配置中心

欢迎使用 oh-my-config！这是一个 LLM Wiki 风格的项目配置管理中心。

## 核心概念

项目将配置组织为三种类型：
- **Wiki** - 项目知识库，AI 可读取来了解项目背景
- **Spec** - 规范文件，如代码规范、CLAUDE.md 等
- **Config** - 服务配置，JSON 格式

## 使用方法

1. 左侧选择项目
2. 顶部切换类型 (Wiki/规范/配置)
3. 左侧点击文件进入编辑
4. Cmd+S 保存或点击保存按钮

## 快捷操作

- 导出到 OpenCode - 复制配置到剪贴板
- 下发到目录 - 同步到项目目录
"""

def ensure_help():
    conn = sqlite3.connect(DB)
    if not conn.execute('SELECT COUNT(*) FROM project').fetchone()[0]:
        conn.execute('INSERT INTO project (name, description) VALUES (?, ?)', ('demo', '示例项目'))
        conn.execute('INSERT INTO config (project, type, name, content) VALUES (?, ?, ?, ?)', 
            ('demo', 'wiki', 'README', HELP_README))
        conn.commit()
    conn.close()

ensure_help()

def mask(content):
    try:
        d = json.loads(content) if isinstance(content, str) else content
        for k, v in d.items() if isinstance(d, dict) else {}:
            if isinstance(v, dict):
                for sk in ['password', 'secret', 'token', 'key']:
                    if sk in v and v.get(sk): v[sk] = '******'
            elif k in ['password', 'secret', 'token', 'key'] and v: d[k] = '******'
        return json.dumps(d) if isinstance(content, str) else d
    except: return content

@app.route('/')
def i(): return send_file('static/index.html')

@app.route('/api/readme')
def get_readme():
    readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as f:
            return f.read()
    return '# oh-my-config\n\nNo README found'

@app.route('/api/folder/read')
def read_folder():
    path = request.args.get('path')
    if not path:
        return jsonify({'error': 'path required'}), 400
    
    path = os.path.expanduser(path)
    if not os.path.exists(path):
        return jsonify({'error': 'Path not found'}), 404
    
    result = []
    try:
        if os.path.isfile(path):
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            return jsonify({'type': 'file', 'content': content, 'path': path})
        else:
            for entry in os.listdir(path):
                full_path = os.path.join(path, entry)
                is_dir = os.path.isdir(full_path)
                result.append({
                    'name': entry,
                    'type': 'dir' if is_dir else 'file',
                    'path': full_path
                })
            result.sort(key=lambda x: (x['type'] == 'file', x['name'].lower()))
            return jsonify({'type': 'folder', 'files': result, 'path': path})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/folder/save', methods=['POST'])
def save_file():
    d = request.json
    path = d.get('path')
    content = d.get('content', '')
    
    if not path:
        return jsonify({'error': 'path required'}), 400
    
    path = os.path.expanduser(path)
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/folder/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    f = request.files['file']
    path = request.form.get('path')
    if not path:
        return jsonify({'error': 'path required'}), 400
    
    path = os.path.expanduser(path)
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        f.save(path)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/projects')
def projects():
    conn = sqlite3.connect(DB)
    rs = conn.execute('SELECT * FROM project ORDER BY name').fetchall()
    conn.close()
    return jsonify([{'id': r[0], 'name': r[1], 'description': r[2]} for r in rs])

@app.route('/api/project', methods=['POST', 'PUT', 'DELETE'])
def add_project():
    if request.method == 'DELETE':
        name = request.args.get('name')
        if not name:
            d = request.json
            name = d.get('name') if d else None
        if not name:
            return jsonify({'error': 'name required'}), 400
        conn = sqlite3.connect(DB)
        conn.execute('DELETE FROM config WHERE project = ?', (name,))
        conn.execute('DELETE FROM project WHERE name = ?', (name,))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    
    if request.method == 'PUT':
        d = request.json
        name = d.get('name')
        if not name:
            return jsonify({'error': 'name required'}), 400
        conn = sqlite3.connect(DB)
        conn.execute('DELETE FROM config WHERE project = ?', (name,))
        conn.execute('DELETE FROM project WHERE name = ?', (name,))
        conn.execute('INSERT INTO project (name, description) VALUES (?, ?)', (name, d.get('description', '')))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    
    d = request.json
    conn = sqlite3.connect(DB)
    conn.execute('INSERT OR IGNORE INTO project (name, description) VALUES (?, ?)', (d.get('name'), d.get('description', '')))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/configs/<p>')
def list_configs(p):
    if p == '_global':
        conn = sqlite3.connect(DB)
        rs = conn.execute("SELECT type, name, content, version, updated_at FROM config WHERE project = '_global' ORDER BY type, name").fetchall()
        conn.close()
    else:
        conn = sqlite3.connect(DB)
        rs = conn.execute('SELECT type, name, content, version, updated_at FROM config WHERE project = ? ORDER BY type, name', (p,)).fetchall()
        conn.close()
    return jsonify([{'type': r[0], 'name': r[1], 'content': mask(r[2]), 'version': r[3], 'updated_at': r[4]} for r in rs])

@app.route('/api/config', methods=['POST', 'PUT'])
def save_config():
    d = request.json
    p, t, n, c = d['project'], d.get('type', 'config'), d.get('name', d['project']), d.get('content', '')
    if p == '_global': p = '_global'
    conn = sqlite3.connect(DB)
    if conn.execute('SELECT 1 FROM config WHERE project=? AND type=? AND name=?', (p, t, n)).fetchone():
        conn.execute('UPDATE config SET content=?, version=version+1, updated_at=datetime("now") WHERE project=? AND type=? AND name=?', (c, p, t, n))
    else:
        conn.execute('INSERT INTO config (project, type, name, content) VALUES (?, ?, ?, ?)', (p, t, n, c))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/config/<p>/<t>/<n>')
def get_config(p, t, n):
    conn = sqlite3.connect(DB)
    r = conn.execute('SELECT content FROM config WHERE project=? AND type=? AND name=?', (p, t, n)).fetchone()
    conn.close()
    return jsonify({'content': r[0] if r else None})

@app.route('/api/sync', methods=['POST'])
def sync():
    d = request.json
    p, t = d['project'], os.path.expanduser(d.get('target', f'~/projects/{d["project"]}'))
    conn = sqlite3.connect(DB)
    rs = conn.execute('SELECT type, name, content FROM config WHERE project = ?', (p,)).fetchall()
    conn.close()
    os.makedirs(t, exist_ok=True)
    
    configs = {'wiki': {}, 'spec': {}, 'config': {}}
    for r in rs:
        try:
            configs[r[0]][r[1]] = json.loads(r[2])
        except:
            configs[r[0]][r[1]] = r[2]
    
    # Sync .ai-config.json
    if configs['config']:
        with open(os.path.join(t, '.ai-config.json'), 'w', encoding='utf-8') as f:
            content = configs['config']
            for k, v in content.items():
                if isinstance(v, str):
                    try:
                        content[k] = json.loads(v)
                    except:
                        pass
            json.dump({'project': p, 'services': content, '_version': 1}, f, indent=2)
    
    # Sync CLAUDE.md (from spec/CLAUDE)
    if 'CLAUDE' in configs['spec']:
        with open(os.path.join(t, 'CLAUDE.md'), 'w', encoding='utf-8') as f:
            f.write(configs['spec']['CLAUDE'])
    
    # Sync AGENTS.md (from spec/AGENTS)
    if 'AGENTS' in configs['spec']:
        with open(os.path.join(t, 'AGENTS.md'), 'w', encoding='utf-8') as f:
            f.write(configs['spec']['AGENTS'])
    
    # Sync GEMINI.md
    if 'GEMINI' in configs['spec']:
        with open(os.path.join(t, 'GEMINI.md'), 'w', encoding='utf-8') as f:
            f.write(configs['spec']['GEMINI'])
    
    # Sync wiki directory
    if configs['wiki']:
        wiki_dir = os.path.join(t, 'wiki')
        os.makedirs(wiki_dir, exist_ok=True)
        
        # Build index for wiki pages
        index_lines = [f'# {p} Wiki\n', '> AI 维护的知识库入口\n', '## 目录\n']
        log_lines = [f'# LOG.md\n', '> AI 探索和发现记录\n', f'## {datetime.now().strftime("%Y-%m-%d")}\n']
        
        for name, content in configs['wiki'].items():
            fname = name + '.md' if not name.endswith('.md') else name
            with open(os.path.join(wiki_dir, fname), 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Generate one-line summary for index
            first_line = content.strip().split('\n')[0] if content.strip() else fname
            summary = first_line.strip('# ').strip()[:80]
            index_lines.append(f'- [{fname}]({fname}) - {summary}\n')
        
        index_lines.extend([
            '\n## 更新日志\n',
            f'- {datetime.now().strftime("%Y-%m-%d")} - 初始化 Wiki\n'
        ])
        
        log_lines.extend([
            '\n### 新发现\n\n- \n',
            '\n### 待整理\n\n- [ ] \n',
            '\n### 问答记录\n\n**Q**: \n**A**: \n'
        ])
        
        with open(os.path.join(wiki_dir, 'INDEX.md'), 'w', encoding='utf-8') as f:
            f.write(''.join(index_lines))
        
        with open(os.path.join(wiki_dir, 'LOG.md'), 'w', encoding='utf-8') as f:
            f.write(''.join(log_lines))
    
    # Create .project-id
    with open(os.path.join(t, '.project-id'), 'w', encoding='utf-8') as f:
        f.write(p)
    
    return jsonify({'success': True, 'synced': list(configs.keys())})

@app.route('/api/search')
def search_api():
    q = request.args.get('q', '').lower()
    if not q:
        return jsonify({'results': []})
    
    results = []
    conn = sqlite3.connect(DB)
    
    # Search configs (name and content)
    rows = conn.execute("""
        SELECT project, type, name, content 
        FROM config 
        WHERE LOWER(name) LIKE ? OR LOWER(content) LIKE ?
        LIMIT 20
    """, (f'%{q}%', f'%{q}%')).fetchall()
    
    for r in rows:
        results.append({
            'project': r[0],
            'type': r[1],
            'name': r[2],
            'file': r[2]
        })
    
    conn.close()
    return jsonify({'results': results})

@app.route('/api/discover')
def discover():
    cwd = os.getcwd()
    pid_file = os.path.join(cwd, '.project-id')
    if os.path.exists(pid_file):
        with open(pid_file) as f:
            project = f.read().strip()
    else:
        project = os.path.basename(cwd)
    
    conn = sqlite3.connect(DB)
    exists = conn.execute('SELECT 1 FROM project WHERE name = ?', (project,)).fetchone()
    if exists:
        rs = conn.execute('SELECT type, name, content FROM config WHERE project = ?', (project,)).fetchall()
    else:
        rs = []
    conn.close()
    
    return jsonify({
        'project': project,
        'exists': bool(exists),
        'configs': [{'type': r[0], 'name': r[1], 'content': mask(r[2])} for r in rs]
    })

@app.route('/api/export')
def export_all():
    p = request.args.get('project')
    if not p:
        return jsonify({'error': 'project required'}), 400
    
    conn = sqlite3.connect(DB)
    rs = conn.execute('SELECT type, name, content FROM config WHERE project = ?', (p,)).fetchall()
    conn.close()
    
    result = {'project': p}
    for r in rs:
        if r[0] not in result:
            result[r[0]] = {}
        try:
            result[r[0]][r[1]] = json.loads(r[2])
        except:
            result[r[0]][r[1]] = r[2]
    
    return jsonify(result)

@app.route('/api/delete', methods=['POST'])
def delete():
    d = request.json
    conn = sqlite3.connect(DB)
    conn.execute('DELETE FROM config WHERE project=? AND type=? AND name=?', (d['project'], d.get('type', 'config'), d.get('name')))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

# ========== Nacos Integration ==========
@app.route('/api/nacos/configs', methods=['GET'])
def nacos_get_configs():
    """从 Nacos 获取配置列表"""
    project = request.args.get('project')
    if not project:
        return jsonify({'error': 'project required'}), 400
    
    # 获取项目的 Nacos 配置
    conn = sqlite3.connect(DB)
    rs = conn.execute("SELECT content FROM config WHERE project=? AND type='config' AND name='NACOS'", (project,)).fetchone()
    conn.close()
    
    if not rs:
        return jsonify({'error': 'Nacos config not found'}), 404
    
    try:
        nacos_conf = json.loads(rs[0])
    except:
        return jsonify({'error': 'Invalid Nacos config'}), 400
    
    server_addr = nacos_conf.get('serverAddr', '')
    namespace = nacos_conf.get('namespace', '')
    username = nacos_conf.get('username', '')
    password = nacos_conf.get('password', '')
    
    if not server_addr:
        return jsonify({'error': 'Nacos serverAddr not configured'}), 400
    
    # 调用 Nacos API 获取配置列表
    try:
        # Nacos 2.x API
        url = f"{server_addr}/nacos/v1/cs/configs?search=accurate&tenant={namespace}"
        auth = (username, password) if username else None
        resp = requests.get(url, auth=auth, timeout=10)
        
        if resp.status_code == 200:
            data = resp.json()
            return jsonify({
                'success': True,
                'configs': data.get('pageItems', []),
                'server': server_addr,
                'namespace': namespace
            })
        else:
            return jsonify({'error': f'Nacos error: {resp.text}'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/nacos/config', methods=['GET', 'POST', 'DELETE'])
def nacos_config():
    """操作 Nacos 单个配置"""
    project = request.args.get('project') or (request.json or {}).get('project')
    data_id = request.args.get('dataId') or (request.json or {}).get('dataId')
    group = request.args.get('group') or (request.json or {}).get('group', 'DEFAULT_GROUP')
    
    if not project or not data_id:
        return jsonify({'error': 'project and dataId required'}), 400
    
    # 获取 Nacos 配置
    conn = sqlite3.connect(DB)
    rs = conn.execute("SELECT content FROM config WHERE project=? AND type='config' AND name='NACOS'", (project,)).fetchone()
    conn.close()
    
    if not rs:
        return jsonify({'error': 'Nacos config not found'}), 404
    
    try:
        nacos_conf = json.loads(rs[0])
    except:
        return jsonify({'error': 'Invalid Nacos config'}), 400
    
    server_addr = nacos_conf.get('serverAddr', '')
    namespace = nacos_conf.get('namespace', '')
    username = nacos_conf.get('username', '')
    password = nacos_conf.get('password', '')
    
    if not server_addr:
        return jsonify({'error': 'Nacos serverAddr not configured'}), 400
    
    auth = (username, password) if username else None
    
    if request.method == 'GET':
        # 获取配置
        url = f"{server_addr}/nacos/v1/cs/configs?dataId={data_id}&group={group}&tenant={namespace}"
        try:
            resp = requests.get(url, auth=auth, timeout=10)
            if resp.status_code == 200 and resp.text:
                return jsonify({
                    'success': True,
                    'dataId': data_id,
                    'group': group,
                    'content': resp.text
                })
            else:
                return jsonify({'error': 'Config not found'}), 404
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    elif request.method == 'POST':
        # 发布配置
        content = (request.json or {}).get('content', '')
        url = f"{server_addr}/nacos/v1/cs/configs"
        params = {
            'dataId': data_id,
            'group': group,
            'content': content,
            'tenant': namespace
        }
        try:
            resp = requests.post(url, params=params, auth=auth, timeout=10)
            if resp.status_code == 200 and resp.text == 'true':
                return jsonify({'success': True, 'message': 'Config published'})
            else:
                return jsonify({'error': f'Publish failed: {resp.text}'}), 500
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    elif request.method == 'DELETE':
        # 删除配置
        url = f"{server_addr}/nacos/v1/cs/configs"
        params = {
            'dataId': data_id,
            'group': group,
            'tenant': namespace
        }
        try:
            resp = requests.delete(url, params=params, auth=auth, timeout=10)
            if resp.status_code == 200 and resp.text == 'true':
                return jsonify({'success': True, 'message': 'Config deleted'})
            else:
                return jsonify({'error': f'Delete failed: {resp.text}'}), 500
        except Exception as e:
            return jsonify({'error': str(e)}), 500

@app.route('/api/nacos/publish', methods=['POST'])
def nacos_publish():
    """发布配置到 Nacos (快捷方式)"""
    d = request.json
    project = d.get('project')
    data_id = d.get('dataId')
    group = d.get('group', 'DEFAULT_GROUP')
    content = d.get('content', '')
    
    if not project or not data_id:
        return jsonify({'error': 'project, dataId, content required'}), 400
    
    # 复用 nacos_config 的逻辑
    conn = sqlite3.connect(DB)
    rs = conn.execute("SELECT content FROM config WHERE project=? AND type='config' AND name='NACOS'", (project,)).fetchone()
    conn.close()
    
    if not rs:
        return jsonify({'error': 'Nacos config not found'}), 404
    
    try:
        nacos_conf = json.loads(rs[0])
    except:
        return jsonify({'error': 'Invalid Nacos config'}), 400
    
    server_addr = nacos_conf.get('serverAddr', '')
    namespace = nacos_conf.get('namespace', '')
    username = nacos_conf.get('username', '')
    password = nacos_conf.get('password', '')
    
    if not server_addr:
        return jsonify({'error': 'Nacos serverAddr not configured'}), 400
    
    url = f"{server_addr}/nacos/v1/cs/configs"
    params = {
        'dataId': data_id,
        'group': group,
        'content': content,
        'tenant': namespace
    }
    auth = (username, password) if username else None
    
    try:
        resp = requests.post(url, params=params, auth=auth, timeout=10)
        if resp.status_code == 200 and resp.text == 'true':
            return jsonify({'success': True, 'message': f'Published to Nacos: {data_id}'})
        else:
            return jsonify({'error': f'Publish failed: {resp.text}'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(port=8848)