# Fix “Permission denied” for uploads (image already running)

Use this when **the Docker image is already running on another system** and you get **permission denied for /app/uploads** when uploading a video. No image rebuild needed.

---

## Option 1: Use updated docker-compose (recommended – works on any system)

The project’s `docker-compose.yml` is set up to avoid upload permission issues:

- **Named volume** for uploads (`smart-cctv-uploads`) so host folder permissions don’t matter.
- Backend runs as **root** so it can always write to `/app/uploads`.

**On the other system:**

1. Get the latest `docker-compose.yml` (e.g. `git pull` or copy the file from this repo).
2. In the project root, recreate the backend so it uses the new settings:

   ```bash
   docker-compose up -d --force-recreate backend
   ```

   Or in Docker Desktop: **Containers** → **smart-cctv-backend** → **⋮** → **Delete** (container only), then run in terminal: `docker-compose up -d`.

3. Try uploading a video again.

**Note:** Uploaded files are stored in Docker’s volume `smart-cctv-uploads`, not in a folder under the project. To copy files out:  
`docker cp smart-cctv-backend:/app/uploads ./uploads-backup`

---

## Option 2: Fix folder access using the host

The backend container runs as user **1000**. The `uploads` folder on the host must be writable by that user.

### On Mac or Linux (Terminal)

Open a terminal in the **project root** (the folder that contains `docker-compose.yml`), then run:

```bash
# Create folders if they don’t exist
mkdir -p uploads backend/uploads

# Give ownership to the container user (uid 1000)
sudo chown -R 1000:1000 uploads backend/uploads

# Restart the backend so it picks up the change
docker-compose restart backend
```

If you don’t have `sudo`, or only need a quick fix for development:

```bash
mkdir -p uploads backend/uploads
chmod -R 777 uploads backend/uploads
docker-compose restart backend
```

---

### On Windows (Docker Desktop)

1. **Open the project folder in File Explorer**  
   Go to the folder that contains `docker-compose.yml` (e.g. `smart-cctv-app`).

2. **Fix permissions for the upload folders**
   - Right‑click **`uploads`** → **Properties** → **Security** tab.
   - Click **Edit** → **Add** → type `Everyone` → **Check names** → OK.
   - Select **Everyone** → tick **Full control** → **Apply** → OK.
   - Repeat for **`backend\uploads`** if that folder exists.

3. **Restart the backend in Docker Desktop**
   - Open **Docker Desktop** → **Containers**.
   - Find **smart-cctv-backend** → click the **⋮** menu → **Restart**.

   Or in PowerShell (in the project root):

   ```powershell
   docker-compose restart backend
   ```

---

## Option 3: Fix using Docker Desktop (one-off container)

If you can’t change host folder permissions, run a one-off container that fixes permissions inside the volume. Use **Docker Desktop → Terminal** or your system terminal in the **project root**.

**Mac/Linux:**

```bash
docker run --rm -v "$(pwd)/uploads:/app/uploads" alpine sh -c "chown -R 1000:1000 /app/uploads && chmod -R 755 /app/uploads"
docker-compose restart backend
```

**Windows (PowerShell):**

```powershell
docker run --rm -v "${PWD}/uploads:/app/uploads" alpine sh -c "chown -R 1000:1000 /app/uploads && chmod -R 755 /app/uploads"
docker-compose restart backend
```

**Note:** This fixes the `uploads` folder. If your app uses `backend/uploads` as the mount, use that path instead:

```bash
# Mac/Linux
docker run --rm -v "$(pwd)/backend/uploads:/app/uploads" alpine sh -c "chown -R 1000:1000 /app/uploads && chmod -R 755 /app/uploads"
```

Then restart the backend as above.

---

## Check that it worked

1. Restart backend (if you haven’t): `docker-compose restart backend`
2. Open the app in the browser and try **uploading a video** again.
3. If it still fails, check backend logs in Docker Desktop: **Containers** → **smart-cctv-backend** → **Logs**.

---

## Summary (other system, Docker Desktop)

**Best:** Use **Option 1** – update `docker-compose.yml` from the repo and run `docker-compose up -d --force-recreate backend`. No host permission changes, works on Windows/Mac/Linux.

**If you can’t change compose:** Use Option 2 (host permissions) or Option 3 (one-off container), then restart the backend. No need to rebuild the image.
