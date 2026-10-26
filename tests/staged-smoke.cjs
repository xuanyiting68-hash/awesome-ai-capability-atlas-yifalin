/* Exercise exactly the artifact that Pages publishes, including deployment.json. */
const {spawn,spawnSync}=require('node:child_process');
const assert=require('node:assert/strict');
const base='http://127.0.0.1:8767/';
let server;
(async()=>{
  const build=spawnSync('python',['scripts/build_site.py'],{stdio:'inherit'});assert.equal(build.status,0);
  server=spawn('python',['-m','http.server','8767','--bind','127.0.0.1','--directory','_site'],{stdio:'ignore'});
  let ready=false;
  for(let i=0;i<40;i++){
    try{if((await fetch(base)).ok){ready=true;break}}catch{}
    await new Promise(resolve=>setTimeout(resolve,100));
  }
  assert.equal(ready,true,'Staged site must start');
  const code=await new Promise(resolve=>spawn(process.execPath,['tests/deployed-smoke.cjs'],{stdio:'inherit',env:{...process.env,ATLAS_BASE_URL:base,EXPECTED_COMMIT:''}}).on('exit',resolve));
  assert.equal(code,0,'Staged deployment smoke checks');
})().catch(e=>{console.error(e);process.exitCode=1}).finally(()=>{if(server)server.kill()});
