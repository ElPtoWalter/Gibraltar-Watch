export default {
  async fetch(request) {
    const url = new URL(request.url);
    const path = decodeURIComponent(url.pathname).toLowerCase();

    const blockedPrefixes = [
      '/.git', '/.github', '/__pycache__', '/node_modules', '/tests', '/test/', '/backup', '/backups'
    ];
    const blockedExtensions = [
      '.json', '.py', '.pyc', '.pyo', '.yml', '.yaml', '.md', '.toml', '.ini', '.cfg', '.env',
      '.log', '.sql', '.zip', '.tar', '.gz', '.7z', '.rar', '.map', '.sh', '.ps1', '.bat'
    ];

    if (blockedPrefixes.some(p => path === p || path.startsWith(p + '/')) || blockedExtensions.some(ext => path.endsWith(ext))) {
      return new Response('Not Found', {
        status: 404,
        headers: {
          'Content-Type': 'text/plain; charset=utf-8',
          'Cache-Control': 'no-store',
          'X-Content-Type-Options': 'nosniff'
        }
      });
    }

    const upstream = await fetch(request);
    const response = new Response(upstream.body, upstream);

    response.headers.set('X-Content-Type-Options', 'nosniff');
    response.headers.set('Referrer-Policy', 'strict-origin-when-cross-origin');
    response.headers.set('X-Frame-Options', 'SAMEORIGIN');
    response.headers.set('Permissions-Policy', 'camera=(), microphone=(), geolocation=(), payment=(), usb=()');
    response.headers.set('Content-Security-Policy', "frame-ancestors 'self'; object-src 'none'; base-uri 'self'; upgrade-insecure-requests");
    response.headers.set('Strict-Transport-Security', 'max-age=31536000');

    if (response.headers.get('content-type')?.includes('text/html')) {
      response.headers.set('Cache-Control', 'public, max-age=0, must-revalidate');
    }

    return response;
  }
};
