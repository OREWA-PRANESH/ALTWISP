(function(){
  function fix(){
    const input=document.querySelector('input[name="language"]');
    if(input){const select=document.createElement('select');select.name='language';select.innerHTML='<option value="auto">Auto</option><option value="en">English</option>';select.value=input.value==='en'?'en':'auto';input.replaceWith(select)}
    const orb=document.querySelector('.mini-orb');
    if(orb&&!orb.querySelector('.mini-fluid')){const fluid=document.createElement('span');fluid.className='mini-fluid';orb.appendChild(fluid)}
  }
  new MutationObserver(fix).observe(document.getElementById('page'),{childList:true,subtree:true});
  fix();
})();
