--------- coverage: platform darwin, python 3.12.11-final-0 ----------
Name                                                Stmts   Miss  Cover   Missing
---

---

app/**init**.py 0 0 100%
app/api/**init**.py 0 0 100%
app/api/dependencies.py 121 11 91% 37-40, 132-133, 158, 166, 168, 171-174
app/api/endpoints/**init**.py 7 0 100%
app/api/endpoints/admin.py 57 0 100%
app/api/endpoints/auth.py 103 3 97% 234-236
app/api/endpoints/email_verification.py 21 0 100%
app/api/endpoints/health.py 9 0 100%
app/api/endpoints/jwks.py 49 4 92% 56-57, 90-91
app/api/endpoints/oauth.py 31 6 81% 44-45, 50-51, 54-55
app/api/endpoints/password_reset.py 39 0 100%
app/api/endpoints/users.py 45 1 98% 36
app/api/endpoints/wallets.py 112 6 95% 140-149, 214, 224
app/celery_app.py 4 0 100%
app/core/**init**.py 0 0 100%
app/core/celery.py 19 1 95% 42
app/core/config.py 84 7 92% 59-67
app/core/database.py 65 15 77% 33, 35, 60, 103-109, 134-142
app/core/error_handling.py 40 0 100%
app/core/logging.py 31 5 84% 33, 75-77, 81
app/core/middleware.py 52 4 92% 118, 122, 126, 130
app/core/prometheus.py 22 0 100%
app/core/security/roles.py 53 0 100%
app/di.py 217 2 99% 362, 390
app/domain/errors.py 5 0 100%
app/domain/schemas/**init**.py 0 0 100%
app/domain/schemas/audit_log.py 25 1 96% 92
app/domain/schemas/auth_roles.py 67 0 100%
app/domain/schemas/auth_token.py 7 0 100%
app/domain/schemas/defi.py 51 0 100%
app/domain/schemas/email_verification.py 6 0 100%
app/domain/schemas/error.py 8 0 100%
app/domain/schemas/historical_balance.py 16 0 100%
app/domain/schemas/jwks.py 22 1 95% 67
app/domain/schemas/jwt.py 20 0 100%
app/domain/schemas/password_reset.py 9 0 100%
app/domain/schemas/portfolio_metrics.py 31 1 97% 17
app/domain/schemas/portfolio_timeline.py 23 0 100%
app/domain/schemas/token.py 14 0 100%
app/domain/schemas/token_balance.py 13 0 100%
app/domain/schemas/token_price.py 9 0 100%
app/domain/schemas/user.py 31 0 100%
app/domain/schemas/wallet.py 22 0 100%
app/main.py 64 1 98% 75
app/models/**init**.py 15 0 100%
app/models/email_verification.py 15 0 100%
app/models/historical_balance.py 17 1 94% 27
app/models/oauth_account.py 17 0 100%
app/models/password_reset.py 15 0 100%
app/models/portfolio_snapshot.py 20 0 100%
app/models/portfolio_snapshot_cache.py 18 0 100%
app/models/refresh_token.py 24 0 100%
app/models/token.py 29 1 97% 35
app/models/token_balance.py 16 1 94% 32
app/models/token_price.py 14 1 93% 30
app/models/transaction.py 19 1 95% 37
app/models/user.py 20 1 95% 51
app/models/wallet.py 26 1 96% 88
app/repositories/**init**.py 9 0 100%
app/repositories/email_verification_repository.py 63 0 100%
app/repositories/historical_balance_repository.py 21 3 86% 43-50
app/repositories/oauth_account_repository.py 48 6 88% 45-52, 79-86
app/repositories/password_reset_repository.py 63 0 100%
app/repositories/portfolio_snapshot_repository.py 123 62 50% 96-104, 131-137, 157-163, 184-194, 210-249, 263-317, 354-401
app/repositories/refresh_token_repository.py 70 0 100%
app/repositories/token_balance_repository.py 21 3 86% 42-49
app/repositories/token_price_repository.py 21 3 86% 38-44
app/repositories/token_repository.py 21 3 86% 42-49
app/repositories/user_repository.py 130 0 100%
app/repositories/wallet_repository.py 91 0 100%
app/services/auth_service.py 136 8 94% 265-266, 279-280, 312-314, 318
app/services/email_service.py 49 33 33% 18-23, 33-58, 74-85, 92-103
app/services/oauth_service.py 52 0 100%
app/tasks/jwt_rotation.py 78 0 100%
app/usecase/**init**.py 0 0 100%
app/usecase/email_verification_usecase.py 71 43 39% 48-98, 107-135
app/usecase/historical_balance_usecase.py 18 0 100%
app/usecase/oauth_usecase.py 121 4 97% 71-77, 267
app/usecase/portfolio_snapshot_usecase.py 42 22 48% 48-52, 65-74, 90-148
app/usecase/token_balance_usecase.py 18 3 83% 50-55
app/usecase/token_price_usecase.py 18 8 56% 31-50
app/usecase/token_usecase.py 18 3 83% 45-50
app/usecase/wallet_usecase.py 155 32 79% 57, 110, 129-137, 151, 197, 219-228, 246, 286-295, 313, 366-367, 396-405, 431, 473-475, 496-506
app/utils/audit.py 12 0 100%
app/utils/encryption.py 26 0 100%
app/utils/jwks_cache.py 56 0 100%
app/utils/jwt.py 137 21 85% 47, 271, 276-279, 288, 299-310, 314, 332, 342, 348-350
app/utils/jwt_keys.py 46 3 93% 50, 116, 121
app/utils/jwt_rotation.py 41 2 95% 40, 102
app/utils/logging.py 114 5 96% 51, 94, 131-134, 213
app/utils/oauth_state_cache.py 25 0 100%
app/utils/rate_limiter.py 22 0 100%
app/utils/redis_lock.py 11 0 100%
app/utils/security.py 13 0 100%
app/utils/token.py 13 0 100%
app/validators/**init**.py 0 0 100%
app/validators/audit_validator.py 12 0 100%
app/validators/security.py 11 0 100%

---

TOTAL 3885 343 91%
