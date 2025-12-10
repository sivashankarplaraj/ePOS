import os
import sys
import shutil
import subprocess
from shutil import which


def run(cmd: list[str], cwd: str | None = None):
    return subprocess.run(cmd, check=True, cwd=cwd)


def docker_available():
    if which("docker") is None:
        return False
    try:
        subprocess.run(["docker", "info"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return True
    except subprocess.CalledProcessError:
        return False


def compose_cmd():
    # Prefer plugin syntax: docker compose
    try:
        subprocess.run(["docker", "compose", "version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return ["docker", "compose"]
    except Exception:
        # Fallback to legacy docker-compose
        if which("docker-compose"):
            return ["docker-compose"]
        # As a last resort, still try plugin; better error surfaced later
        return ["docker", "compose"]


def ensure_dir_clean(path: str):
    os.makedirs(path, exist_ok=True)
    for f in os.listdir(path):
        fp = os.path.join(path, f)
        if os.path.isfile(fp):
            os.remove(fp)
        elif os.path.isdir(fp):
            shutil.rmtree(fp, ignore_errors=True)


def make_zip(src_dir: str, zip_path: str):
    # Cross-platform zip creation
    base, _ = os.path.splitext(zip_path)
    # Parent of src_dir is project_root; shutil.make_archive wants base name without extension
    # It will create base + ".zip" at the parent directory of src_dir
    parent = os.path.dirname(src_dir)
    name = os.path.basename(base)
    # Temporarily change working directory so the archive contains docker_build_files/*
    cwd = os.getcwd()
    try:
        os.chdir(parent)
        shutil.make_archive(name, 'zip', root_dir=parent, base_dir=os.path.basename(src_dir))
    finally:
        os.chdir(cwd)


def main():
    if not docker_available():
        raise SystemExit("Docker daemon is not running or Docker CLI not found. Please start Docker Desktop/Service and retry.")

    comp = compose_cmd()
    # Project root is one level up from scripts/
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    compose_file = os.path.join(project_root, 'compose.yml')

    # Compose down (ignore errors if nothing is running). Also remove local images/volumes
    try:
        # Remove stopped containers, local images built by compose, and volumes to avoid size creep
        run(comp + ["-f", compose_file, "down", "--rmi", "local", "--volumes"], cwd=project_root)
    except subprocess.CalledProcessError:
        pass

    # Proactively remove previously built tags if they exist (ignore failures)
    for tag in ("epos_web:latest", "epos-web:latest"):
        try:
            run(["docker", "rmi", tag])
        except subprocess.CalledProcessError:
            pass

    # Prune dangling images and builder cache to prevent incremental growth
    try:
        run(["docker", "image", "prune", "-f"])
    except subprocess.CalledProcessError:
        pass
    try:
        run(["docker", "builder", "prune", "-f"])
    except subprocess.CalledProcessError:
        pass

    # Build image with explicit target platform via buildx for portability
    # Default to linux/amd64 to match most PCs, allow override via EPOS_BUILD_PLATFORM
    target_platform = os.environ.get("EPOS_BUILD_PLATFORM", "linux/amd64")
    use_no_cache = os.environ.get("EPOS_DOCKER_NO_CACHE", "0") in ("1", "true", "True")
    # Ensure buildx is available; create/use a builder if needed
    try:
        subprocess.run(["docker", "buildx", "version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    except subprocess.CalledProcessError:
        raise SystemExit("Docker buildx is required to build for specific platforms. Please enable Docker Buildx and retry.")

    # Create and use a named builder (idempotent)
    try:
        run(["docker", "buildx", "create", "--name", "epos_builder"])
    except subprocess.CalledProcessError:
        pass
    try:
        run(["docker", "buildx", "use", "epos_builder"])
    except subprocess.CalledProcessError:
        pass

    build_cmd = [
        "docker", "buildx", "build",
        "--platform", target_platform,
        "-t", "epos-web:latest",
        "-f", os.path.join(project_root, "Dockerfile"),
        "--load"  # load image into local docker after buildx
    ]
    if use_no_cache:
        build_cmd += ["--no-cache"]
    build_cmd += [project_root]
    run(build_cmd, cwd=project_root)

    # Prepare output directory
    output_dir = os.path.join(project_root, 'docker_build_files')
    ensure_dir_clean(output_dir)

    # Save image tar (use cross-platform stdout pipe)
    output_tar = os.path.join(output_dir, 'epos_docker.tar')
    with open(output_tar, 'wb') as f:
        # Try common tags: underscore and hyphen variants
        for tag in ("epos_web:latest", "epos-web:latest"):
            proc = subprocess.Popen(["docker", "save", tag], stdout=f)
            ret = proc.wait()
            if ret == 0:
                break
        else:
            raise SystemExit("Failed to save Docker image (tried epos_web:latest and epos-web:latest). Ensure compose build produces the expected tag.")

    # Copy environment file(s). Prefer .env, fallback to env. Also include both names in bundle.
    env_dst = os.path.join(output_dir, '.env')
    env_src_candidates = [
        os.path.join(project_root, '.env'),
        os.path.join(project_root, 'env'),
    ]
    copied_env = False
    for env_src in env_src_candidates:
        if os.path.exists(env_src):
            shutil.copy(env_src, env_dst)
            copied_env = True
            break
    if not copied_env:
        # create an empty placeholder to avoid missing file errors when loading env
        open(env_dst, 'a').close()
    # Also create a non-dot alias 'env' for consumers expecting that filename
    env_dst_alias = os.path.join(output_dir, 'env')
    try:
        shutil.copy(env_dst, env_dst_alias)
    except Exception:
        # ensure alias exists even if copy fails for some reason
        if not os.path.exists(env_dst_alias):
            open(env_dst_alias, 'a').close()

    # Copy run script
    run_docker_src = os.path.join(project_root, 'scripts', 'run_docker.sh')
    run_docker_dst = os.path.join(output_dir, 'run_docker.sh')
    if os.path.exists(run_docker_src):
        shutil.copy(run_docker_src, run_docker_dst)
    # Also include the cross-platform run script variant
    run_img_src = os.path.join(project_root, 'scripts', 'run_docker_img.sh')
    run_img_dst = os.path.join(output_dir, 'run_docker_img.sh')
    if os.path.exists(run_img_src):
        shutil.copy(run_img_src, run_img_dst)

    # Create zip cross-platform (delete previous if exists)
    zip_file = os.path.join(project_root, 'epos_docker_build.zip')
    try:
        if os.path.exists(zip_file):
            os.remove(zip_file)
    except Exception:
        pass
    make_zip(output_dir, zip_file)
    print(f"Docker image and .env have been packaged into {zip_file}")
    """
    ls -lh docker_build_files/epos_docker.tar
    ls -lh epos_docker_build.zip
    """


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as e:
        # Provide clearer error with command context
        print(f"Command failed: {getattr(e, 'cmd', '')}")
        sys.exit(e.returncode if hasattr(e, 'returncode') else 1)