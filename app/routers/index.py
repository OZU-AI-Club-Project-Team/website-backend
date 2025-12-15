from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

# Routerlar
from app.modules.auth.auth_router import router as authRouter
from app.modules.user.user_router import router as userRouter
from app.modules.application import router as applicationRouter


def setup_app(app: FastAPI) -> None:
    """
    Tüm middleware ve router'ları FastAPI app'ine bağlayan fonksiyon.
    main.py tarafında sadece bu fonksiyon çağrılacak.
    """

    # ========= MIDDLEWARE =========
    @app.middleware("http")
    async def simple_logging_middleware(request: Request, call_next):
        # Buraya:
        # - request loglama
        # - custom header ekleme
        # - language / tenant vs. çıkarma
        # gibi işler konulacak

        # Cookie'deki access_token bearer header'na çevrildi
        access_token = request.cookies.get("access_token")

        if access_token:
            headers = list(request.scope.get("headers") or [])
            has_auth = any(k.lower() == b"authorization" for k, _ in headers)
            if not has_auth:
                headers.append((b"authorization", f"Bearer {access_token}".encode()))
                request.scope["headers"] = headers

        # ~~SECURITY HEADERS~~

        response = await call_next(request)

        # 1) Temel güvenlik header'ları
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"  # clickjacking'e karşı
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # 2) HSTS / Lokal geliştirmede sorun çıkarsa kaldırılabilir
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains; preload"
        )

        # 3) Permissions-Policy (Feature-Policy)
        response.headers["Permissions-Policy"] = (
            "geolocation=(), "
            "microphone=(), "
            "camera=(), "
            "payment=(), "
            "fullscreen=(self)"
            # Tarayıcı API'larını, özellikle mobil/browser'da kısıtlıyoruz.
            # fullscreen sadece kendi siten için açık
            # =() şeklindeki izinler yasak. Mesela mikrofon kullanılmayacak.
        )

        # 4) İzolasyon (COOP / COEP / CORP)
        # Frontend ile uyumlu hale getirilecek

        """
        response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
        response.headers["Cross-Origin-Embedder-Policy"] = "require-corp"
        response.headers["Cross-Origin-Resource-Policy"] = "same-origin"
        """

        # 5) Content Security Policy (CSP)
        # PROJEYE göre özelleştirilecek

        # response.headers["Content-Security-Policy"] = CSP_POLICY
        return response

    # Buraya global exception handler da eklenebilir
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        # prod’da burada loglama yapılacak
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )

    # ========= ROUTERLAR =========
    app.include_router(authRouter)
    app.include_router(userRouter)
    app.include_router(applicationRouter)
