
(function(){
  function ready(fn){ if(document.readyState !== 'loading'){ fn(); } else { document.addEventListener('DOMContentLoaded', fn); } }
  ready(function(){
    var nav = document.querySelector('.gwc-site-nav') || document.querySelector('.site-nav');
    var toggle = document.querySelector('.nav-toggle');
    if(toggle && nav){
      toggle.addEventListener('click', function(){
        var open = nav.classList.toggle('is-open');
        toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
      });
      nav.querySelectorAll('a').forEach(function(a){
        a.addEventListener('click', function(){
          if(window.innerWidth <= 1180){ nav.classList.remove('is-open'); toggle.setAttribute('aria-expanded','false'); }
        });
      });
    }
    var groups = Array.prototype.slice.call(document.querySelectorAll('.gwc-nav-group'));
    groups.forEach(function(group){
      var summary = group.querySelector('summary');
      if(!summary) return;
      summary.addEventListener('click', function(ev){
        ev.preventDefault();
        var open = group.hasAttribute('open');
        groups.forEach(function(other){ if(other !== group) other.removeAttribute('open'); });
        if(open) group.removeAttribute('open');
        else group.setAttribute('open','');
      });
    });
    document.addEventListener('click', function(ev){
      if(!ev.target.closest('.gwc-nav-group')){
        groups.forEach(function(group){ group.removeAttribute('open'); });
      }
      if(window.innerWidth <= 1180 && nav && toggle && !ev.target.closest('.site-header')){
        nav.classList.remove('is-open');
        toggle.setAttribute('aria-expanded','false');
      }
    });
    window.addEventListener('resize', function(){
      if(window.innerWidth > 1180 && nav && toggle){
        nav.classList.remove('is-open');
        toggle.setAttribute('aria-expanded','false');
      }
    });
  });
})();
