import type { Request, Response } from 'express';
import { Readable } from 'node:stream';
import type { ReadableStream as NodeReadableStream } from 'node:stream/web';

/**
 * Le front appelle l'API par un chemin relatif (/api/...) : ce serveur transmet la requête à
 * l'adresse donnée par API_UPSTREAM, lue au lancement. Aucune adresse d'environnement n'est dans
 * le code ni dans l'image, ce qui permet de promouvoir la même image du staging à la production.
 */
const API_UPSTREAM = (process.env['API_UPSTREAM'] ?? 'http://api:8000').replace(/\/+$/, '');

// En-têtes propres à une connexion, jamais transmis. content-length et content-encoding sont aussi
// retirés : fetch a déjà décompressé le corps, qui est renvoyé en flux.
const HOP_BY_HOP = new Set([
  'connection',
  'keep-alive',
  'proxy-authenticate',
  'proxy-authorization',
  'te',
  'trailer',
  'transfer-encoding',
  'upgrade',
  'host',
  'content-length',
  'content-encoding',
]);

export async function apiProxy(req: Request, res: Response): Promise<void> {
  const headers = new Headers();
  for (const [name, value] of Object.entries(req.headers)) {
    if (value === undefined || HOP_BY_HOP.has(name)) continue;
    headers.set(name, Array.isArray(value) ? value.join(', ') : value);
  }
  headers.set('x-forwarded-host', req.headers.host ?? '');
  headers.set('x-forwarded-proto', req.protocol);

  const hasBody = req.method !== 'GET' && req.method !== 'HEAD';
  const init: RequestInit & { duplex?: 'half' } = {
    method: req.method,
    headers,
    redirect: 'manual',
  };
  if (hasBody) {
    init.body = Readable.toWeb(req) as unknown as BodyInit;
    init.duplex = 'half';
  }

  try {
    // Monté sous /api, Express a déjà retiré ce préfixe de req.url.
    const upstream = await fetch(`${API_UPSTREAM}${req.url}`, init);

    res.status(upstream.status);
    upstream.headers.forEach((value, name) => {
      if (!HOP_BY_HOP.has(name) && name !== 'set-cookie') res.setHeader(name, value);
    });
    const cookies = upstream.headers.getSetCookie();
    if (cookies.length > 0) res.setHeader('set-cookie', cookies);

    if (upstream.body) {
      Readable.fromWeb(upstream.body as unknown as NodeReadableStream)
        .on('error', () => res.destroy())
        .pipe(res);
    } else {
      res.end();
    }
  } catch (error) {
    console.error(`API injoignable (${API_UPSTREAM}) :`, error);
    if (!res.headersSent) res.status(502).json({ detail: 'API injoignable' });
  }
}
