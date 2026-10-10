from .base import *

if os.environ.get("USE_SQLITE_TEST_DB") == "1":
	DATABASES["default"] = {
		"ENGINE": "django.db.backends.sqlite3",
		"NAME": BASE_DIR / "test.sqlite3",
	}

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]