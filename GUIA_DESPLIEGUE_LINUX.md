# Guía Completa de Instalación y Despliegue para aevi.lat en Linux Debian

Esta guía paso a paso te permitirá clonar, configurar y desplegar la aplicación `xmlPaper` en tu servidor **Debian** utilizando **Docker**, **Apache2** como Proxy Inverso y certificado **SSL/HTTPS** gratis con **Certbot** para el dominio **`aevi.lat`**.

---

## 📋 Resumen de la Arquitectura

- **Dominio:** `https://aevi.lat` (y `https://www.aevi.lat`)
- **Backend / API:** Docker Contenedor (`xmlpaper`) escuchando en `http://127.0.0.1:8000`
- **Web Server / Proxy Inverso:** Apache2 en Debian (recibe en puertos 80 y 443)
- **Certificado SSL:** Certbot (Let's Encrypt con renovación automática)

---

## PASO 1: Configurar los Registros DNS de tu Dominio (`aevi.lat`)

Antes de comenzar en el servidor, ingresá al panel donde administras tu dominio `aevi.lat` (Cloudflare DNS, Namecheap, GoDaddy, etc.) y agregá los siguientes dos registros **A**:

| Tipo | Nombre (Host) | Valor / Destino | TTL |
| :--- | :--- | :--- | :--- |
| **A** | `@` | `TU_IP_PUBLICA_DEL_SERVIDOR` | Auto |
| **A** | `www` | `TU_IP_PUBLICA_DEL_SERVIDOR` | Auto |

*(Reemplazá `TU_IP_PUBLICA_DEL_SERVIDOR` por la dirección IP de tu servidor Debian).*

---

## PASO 2: Instalar Docker y Herramientas del Sistema en Debian

Conectate por SSH o terminal a tu servidor Debian y ejecutá:

```bash
# 1. Actualizar repositorios del sistema
sudo apt update && sudo apt upgrade -y

# 2. Instalar Git, Curl y Docker
sudo apt install -y git curl docker.io docker-compose-v2

# 3. Dar permisos a tu usuario para usar Docker sin sudo
sudo usermod -aG docker $USER
```

> **Nota:** Después de agregar tu usuario al grupo `docker`, cerrá sesión SSH (`exit`) y volvé a entrar para que apliquen los cambios de usuario.

---

## PASO 3: Clonar el Proyecto y Configurar `.env`

```bash
# 1. Clonar el repositorio
git clone https://github.com/adrianEVI/xmlPaper.git
cd xmlPaper

# 2. Crear el archivo de configuración de variables de entorno
nano .env
```

Dentro del archivo `.env`, agregá tu clave de API de Gemini:

```env
GEMINI_API_KEY=tu_clave_de_api_de_gemini_aqui
```

Guardá el archivo presionando `Ctrl + O`, `Enter` y salí con `Ctrl + X`.

---

## PASO 4: Levantar la Aplicación en Docker

Desde la carpeta del proyecto (`/home/tu_usuario/xmlPaper`), ejecutá:

```bash
docker compose up -d --build
```

Podés verificar que el contenedor esté corriendo correctamente con:

```bash
docker compose ps
```

---

## PASO 5: Instalar y Configurar Apache2 como Proxy Inverso

```bash
# 1. Instalar Apache2 y activar los módulos de proxy
sudo apt update
sudo apt install -y apache2
sudo a2enmod proxy proxy_http headers rewrite
sudo systemctl restart apache2

# 2. Crear el archivo de configuración para aevi.lat
sudo nano /etc/apache2/sites-available/aevi.lat.conf
```

Pegá el siguiente contenido dentro de `/etc/apache2/sites-available/aevi.lat.conf`:

```apache
<VirtualHost *:80>
    ServerName aevi.lat
    ServerAlias www.aevi.lat

    ProxyPreserveHost On
    ProxyPass / http://127.0.0.1:8000/
    ProxyPassReverse / http://127.0.0.1:8000/

    ErrorLog ${APACHE_LOG_DIR}/aevi_lat_error.log
    CustomLog ${APACHE_LOG_DIR}/aevi_lat_access.log combined
</VirtualHost>
```

Guardá con `Ctrl + O`, `Enter` y salí con `Ctrl + X`.

Habilitá el nuevo sitio y desactivá la página por defecto:

```bash
sudo a2ensite aevi.lat.conf
sudo a2dissite 000-default.conf
sudo systemctl reload apache2
```

---

## PASO 6: Instalar Certificado SSL / HTTPS Gratis con Certbot

Para habilitar el candado de seguridad (`https://aevi.lat`):

```bash
# 1. Instalar Certbot y el plugin para Apache
sudo apt install -y certbot python3-certbot-apache

# 2. Obtener y configurar el certificado automáticamente
sudo certbot --apache -d aevi.lat -d www.aevi.lat
```

Durante la instalación de Certbot:
- Te pedirá un correo electrónico para avisos de renovación.
- Aceptá los términos y condiciones (`Y`).
- Elegí la opción de redirigir todo el tráfico HTTP a HTTPS si te lo pregunta.

---

## PASO 7: Verificación y Mantenimiento

¡Felicitaciones! Tu aplicación ya está en vivo en **`https://aevi.lat`**.

### Comandos útiles para mantenimiento futuro:

- **Ver logs de la aplicación en Docker:**
  ```bash
  docker compose logs -f
  ```
- **Reiniciar la aplicación:**
  ```bash
  docker compose restart
  ```
- **Actualizar código y reconstruir:**
  ```bash
  git pull
  docker compose up -d --build
  ```
- **Verificar estado de Apache:**
  ```bash
  sudo systemctl status apache2
  ```
