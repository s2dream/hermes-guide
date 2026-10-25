(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const labels = {queued:'대기 중',running:'조사 중',cancelling:'중단 중',cancelled:'중단됨',completed:'완료',insufficient_evidence:'근거 부족',failed:'실패',interrupted:'실행 중단'};
  const finished = new Set(['completed','insufficient_evidence','failed','cancelled','interrupted']);
  const states = {announced:'발표됨',proposed:'제안',scheduled:'예정',completed:'완료',conditional:'조건부',unknown:'미상',instruction_announced:'지시 발표',dialogue_requested:'대화 요청',funding_planned:'재정 확보 예정',meeting_held:'회의 개최',legislation_proposed:'입법 제안',policy_menu_proposed:'특례 제안',talks_proposed:'회담 제안',agenda_proposed:'의제 제안',conditional_option:'조건부 선택지',details_to_consult:'세부 협의 예정',award_results_announced:'수상 결과 발표',award_winner:'수상',special_mention:'특별 언급',nomination_teaser:'후보 공개 예고',nomination_content_published:'후보 콘텐츠 게시',scheduled_event:'행사 예정',presale_start_announced:'예약 판매 시작 공지',scheduled_release:'발매 예정',product_announced:'작품 공지'};
  Object.assign(states,{announced_design:'특례 구상 발표',awarded:'수상',funding_plan:'재정 확보 계획',legislative_plan:'입법 추진 계획',meeting_reported:'회의 개최 발표',nominee_content_published:'후보 콘텐츠 게시',official_position:'공식 입장',proposed_agenda:'제안된 의제'});
  let backend = false, user = null, job = null, epoch = 0, timer, blobURL, pending;
  const node = (tag, text, cls) => { const el = document.createElement(tag); if (text !== undefined) el.textContent = text; if (cls) el.className = cls; return el; };
  function notice(text) { $('notice').textContent = text || ''; $('notice').hidden = !text; }
  function safeLink(url, label) {
    const el = node('a', label);
    try { const parsed = new URL(url); if (parsed.protocol !== 'https:') return node('span', label); el.href = parsed.href; }
    catch { return node('span', label); }
    el.target = '_blank'; el.rel = 'noopener noreferrer'; return el;
  }
  async function api(path, options = {}) {
    const response = await fetch(path, {credentials:'same-origin',...options,headers:{'Content-Type':'application/json',...(options.headers || {})}});
    const data = await response.json();
    if (!response.ok) { if (response.status === 401) setUser(null); throw new Error(data.error || '요청을 처리하지 못했습니다.'); }
    return data;
  }
  function setUser(value) {
    user = value; $('login-panel').hidden = !backend || !!user; $('account').hidden = !user;
    $('user-name').textContent = user ? `${user.name}의 조사 공간` : '';
    $('history-help').textContent = user ? '이 계정으로 실행한 최근 조사입니다.' : '로컬 서버에 로그인하면 이력을 저장합니다.';
    if (!user) { clearTimeout(timer); epoch++; job = null; $('history-list').replaceChildren(); clearReport(); }
  }
  function modeChanged() {
    const live = $('research-mode').value === 'live';
    $('question').readOnly = !live; $('start-date').readOnly = !live; $('end-date').readOnly = !live;
    $('submit-research').textContent = live ? '조사 시작' : '사례 불러오기';
    $('mode-help').textContent = live ? '조사당 최대 검색 4회·원문 읽기 8회·실행 5분. 공급자 요금이 발생할 수 있으며 실제 비용은 아직 집계하지 않습니다.' : '2026-10-25 작성 사례입니다. 새 검색이나 Hermes 실행 없이 기존 결과를 표시합니다.';
    if (!live) { $('start-date').value = '2026-10-01'; $('end-date').value = '2026-10-25'; }
    else { const today = new Date().toLocaleDateString('en-CA',{timeZone:'Asia/Seoul'}); const day = new Date(); day.setUTCDate(day.getUTCDate()-7); $('end-date').value = /^\d{4}-/.test(today) ? today : new Date().toISOString().slice(0,10); $('start-date').value = day.toISOString().slice(0,10); }
    $('question').value = $('domain').value === 'politics' ? '정치·정책 발표에서 지시·제안·시행 여부를 구분하고 출처를 정리해줘.' : '연예·문화 소식에서 수상 결과와 후보·향후 일정을 구분하고 출처를 정리해줘.';
  }
  function clearReport() {
    $('report').replaceChildren(); $('report').hidden = true; $('empty-result').hidden = false;
    $('job-events').hidden = true; $('cancel-research').hidden = true; $('download-report').hidden = true; $('job-status').textContent = '시작 전';
    if (blobURL) { URL.revokeObjectURL(blobURL); blobURL = null; }
  }
  function renderReport(report, localJob) {
    const container = $('report'); container.replaceChildren(); container.hidden = false;
    container.append(node('p', report.mode === 'demo' ? '기존 사례 체험 · 2026-10-25 기준 · Hermes 미실행' : 'Hermes 실제 조사 · 출처·발췌 구조 검사 완료','report-label'),node('h3',report.title),node('p',report.summary,'report-summary'));
    container.append(node('h4',`핵심 주장 ${report.claims.length}개`));
    const claims = node('ol',undefined,'report-claims');
    for (const claim of report.claims) {
      const item = node('li'); item.append(node('p',claim.text));
      item.append(node('p',`상태: ${states[claim.state] || '원문 확인 필요'} · 사건일: ${claim.event_at || '미상'}`,'claim-meta'));
      for (const id of claim.source_ids) { const link = node('a',`[${id}]`); link.href = `#report-source-${id}`; item.append(link); }
      if (claim.evidence?.length) { const detail = node('details'); detail.append(node('summary','원문 발췌 확인')); for (const evidence of claim.evidence) detail.append(node('blockquote',`${evidence.source_id}: ${evidence.quote}`)); item.append(detail); }
      if (claim.limits) item.append(node('p',claim.limits,'claim-meta'));
      claims.append(item);
    }
    container.append(claims,node('h4','확인한 출처'));
    const sources = node('ul',undefined,'report-sources');
    for (const source of report.sources) {
      const item = node('li'); item.id = `report-source-${source.id}`;
      item.append(safeLink(source.url,`[${source.id}] ${source.title}`));
      item.append(node('p',`${source.publisher || ''} · 게시일: ${source.published_at || '미상'} · 조회: ${source.retrieved_at || '미상'}`));
      if (source.attachment_url) item.append(safeLink(source.attachment_url,'공식 첨부 원문'));
      sources.append(item);
    }
    const limits = node('ul',undefined,'report-limits'); for (const text of report.limitations) limits.append(node('li',text));
    container.append(sources,node('h4','확인 한계'),limits,node('p',report.mode === 'demo' ? '이 결과는 기존 편집 사례를 재표시합니다.' : '인용 검사는 사실 정확도 측정이 아닙니다. 토큰·비용은 미측정입니다.','field-help'));
    const download = $('download-report');
    if (blobURL) URL.revokeObjectURL(blobURL);
    if (localJob) download.href = `/api/research/${localJob.id}/download`;
    else { blobURL = URL.createObjectURL(new Blob([JSON.stringify(report,null,2)],{type:'application/json'})); download.href = blobURL; }
    download.download = 'research-report.json'; download.hidden = false;
  }
  function showJob(value) {
    job = value; $('empty-result').hidden = true; $('job-status').textContent = labels[value.state] || value.state;
    $('cancel-research').hidden = finished.has(value.state); $('cancel-research').disabled = value.state === 'cancelling';
    const events = $('job-events'); events.replaceChildren(); events.hidden = false;
    for (const event of value.events || []) events.append(node('li',event.message));
    if (value.result) renderReport(value.result,value);
    if (value.error) notice(value.error);
  }
  async function history() {
    if (!user) return;
    const owner = user.id, data = await api('/api/research'); if (!user || owner !== user.id) return;
    const list = $('history-list'); list.replaceChildren();
    for (const value of data.jobs) { const item = node('li'), button = node('button'); button.type = 'button'; button.append(node('span',value.request.question.slice(0,65)),node('small',`${labels[value.state]} · ${value.created_at.slice(0,10)} · ${value.request.mode === 'demo' ? '사례 체험' : '실제 조사'}`)); button.addEventListener('click',()=>watch(value.id)); item.append(button); list.append(item); }
    if (!data.jobs.length) list.append(node('li','저장한 조사가 없습니다.'));
  }
  function watch(id) {
    const current = ++epoch; clearTimeout(timer); clearReport(); notice('');
    async function poll() {
      try { const value = await api(`/api/research/${id}`); if (current !== epoch) return; showJob(value); if (!finished.has(value.state)) timer = setTimeout(poll,1000); else await history(); }
      catch (error) { if (current === epoch) notice(`${error.message} 이력에서 다시 열어 상태를 확인하세요.`); }
    }
    poll();
  }
  async function snapshot(request) {
    const response = await fetch('data/news-case-studies-2026-10-25.json'); if (!response.ok) throw new Error('사례 데이터를 불러오지 못했습니다.');
    const data = await response.json(), claims = data.claims.filter(c=>c.domain === request.domain), ids = new Set(claims.flatMap(c=>c.source_ids));
    return {title:request.domain === 'politics' ? '정치·정책 사례 브리핑' : '연예·문화 사례 브리핑',mode:'demo',hermes_executed:false,reference_date:data.metadata.reference_date,summary:'2026-10-25에 작성한 기존 사례입니다. 새 질문에 대한 검색·Hermes 실행 결과가 아닙니다.',claims,sources:data.sources.filter(s=>ids.has(s.id)),limitations:data.metadata.limitations,usage:null};
  }
  $('research-form').addEventListener('submit',async event=>{
    event.preventDefault(); notice(''); $('submit-research').disabled = true;
    const request = {question:$('question').value,domain:$('domain').value,mode:$('research-mode').value,start_date:$('start-date').value,end_date:$('end-date').value};
    try {
      if (request.start_date > request.end_date) throw new Error('시작일은 종료일보다 늦을 수 없습니다.');
      if (backend && user) {
        const encoded = JSON.stringify(request); if (!pending || pending.body !== encoded) pending = {body:encoded,key:crypto.randomUUID()};
        const created = await api('/api/research',{method:'POST',body:encoded,headers:{'Idempotency-Key':pending.key}}); pending = null; watch(created.id); await history();
      } else {
        if (request.mode !== 'demo') throw new Error('로컬 서버에 로그인한 뒤 실제 조사를 시작하세요.');
        const report = await snapshot(request); epoch++; clearTimeout(timer); job = null; clearReport(); $('empty-result').hidden = true; $('job-status').textContent = '사례 불러옴'; renderReport(report);
      }
    } catch (error) { notice(error.message); }
    finally { $('submit-research').disabled = false; }
  });
  $('login-form').addEventListener('submit',async event=>{
    event.preventDefault(); notice('');
    try { const result = await api('/api/login',{method:'POST',body:JSON.stringify({token:$('invite-token').value})}); $('invite-token').value = ''; setUser(result.user); await history(); }
    catch (error) { notice(error.message); }
  });
  $('logout').addEventListener('click',async()=>{ try { await api('/api/logout',{method:'POST',body:'{}'}); pending = null; setUser(null); } catch(error) { notice(error.message); } });
  $('cancel-research').addEventListener('click',async()=>{ if (!job) return; const id = job.id; try { const value = await api(`/api/research/${id}/cancel`,{method:'POST',body:'{}'}); if (job?.id === id) showJob(value); } catch(error) { notice(error.message); } });
  $('research-mode').addEventListener('change',modeChanged); $('domain').addEventListener('change',modeChanged);
  async function init() {
    if (location.hostname !== '127.0.0.1') return;
    try {
      const health = await api('/api/health'); if (health.service !== 'hermes-research-pilot') return;
      backend = true; setUser(null);
      $('environment').textContent = health.live.configured ? '로컬 파일럿 · 실제 조사 설정 있음 · 정기 실행 없음' : `로컬 파일럿 · 실제 조사 미설정: ${health.live.missing.join(', ')} · 정기 실행 없음`;
      $('research-mode').options[1].disabled = !health.live.configured; $('research-mode').options[1].textContent = health.live.configured ? 'Hermes 실제 조사' : 'Hermes 실제 조사 · 서버 설정 필요';
      try { setUser((await api('/api/me')).user); await history(); } catch { /* Signed out. */ }
    } catch { /* A static preview can still show the dated editorial examples. */ }
  }
  init();
})();
