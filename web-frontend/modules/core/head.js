export default {
  // MusicEngine: Updated page titles
  title: 'MusicEngine',
  titleTemplate: '%s | MusicEngine',
  // MusicEngine: Inline script to apply theme immediately before render to prevent FOUC
  script: [
    {
      hid: 'theme-init',
      innerHTML: `(function(){try{var u=new URLSearchParams(window.location.search),p=u.get('theme');var t=(p==='light'||p==='dark')?p:(localStorage.getItem('isrc-theme')||'light');if(p)localStorage.setItem('isrc-theme',t);document.documentElement.classList.add('theme-'+t)}catch(e){}})()`,
      type: 'text/javascript',
      charset: 'utf-8',
    },
  ],
  __dangerouslyDisableSanitizersByTagID: {
    'theme-init': ['innerHTML'],
  },
  meta: [
    { charset: 'utf-8' },
    {
      name: 'viewport',
      content:
        'width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no',
    },
    {
      name: 'format-detection',
      content: 'telephone=no, email=no, address=no, date=no',
    },
  ],
  link: [
    {
      rel: 'icon',
      type: 'image/png',
      href: '/img/favicon_16.png',
      sizes: '16x16',
      hid: true,
    },
    {
      rel: 'icon',
      type: 'image/png',
      href: '/img/favicon_32.png',
      sizes: '32x32',
      hid: true,
    },
    {
      rel: 'icon',
      type: 'image/png',
      href: '/img/favicon_48.png',
      sizes: '64x64',
      hid: true,
    },
    {
      rel: 'icon',
      type: 'image/png',
      href: '/img/favicon_192.png',
      sizes: '192x192',
      hid: true,
    },
  ],
}
