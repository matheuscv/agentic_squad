# PATCH para backend/app/main.py — adicionar após os imports e routers existentes:
#
# from app.routers.contatos import router as contatos_router
# app.include_router(contatos_router)
#
# Observação: o prefix "/contatos" e a tag "Contatos" já estão definidos
# dentro do próprio router (routers/contatos.py), portanto NÃO é necessário
# passar prefix ou tags no include_router. Apenas:
#
#   app.include_router(contatos_router)
#
# Substitui o bloco comentado existente no main.py:
#   # TODO TASK-04: incluir router de contatos
#   # from app.routers.contatos import router as contatos_router
#   # app.include_router(contatos_router, prefix="/contatos", tags=["contatos"])
