# Conectar el formulario de newsletter

vNext ya genera cada día el contenido preparado en:

- `newsletter/latest.html`
- `newsletter/latest.txt`
- `newsletter/latest.json`

La web actual ya tiene arquitectura para un endpoint de newsletter mediante `window.GW_BUSINESS_CONFIG`. El paquete **no activa un endpoint ficticio** porque una suscripción real debe gestionar consentimiento, bajas y privacidad.

Cuando dispongas de un endpoint real, modifica únicamente la sección newsletter de `gw-monetization-config.js`:

```js
newsletter: {
  enabled: true,
  endpoint: "https://TU-ENDPOINT-REAL",
  method: "POST"
}
```

El endpoint debe aceptar el campo `email`. Antes de activar el envío real conviene comprobar también el texto de privacidad y el mecanismo de baja del proveedor elegido.

Hasta entonces se mantiene el alta por correo como fallback, de modo que no se muestra al usuario una falsa suscripción automática.
