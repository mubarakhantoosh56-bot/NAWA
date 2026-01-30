from fastapi import FastAPI

app = FastAPI(title="AIMX API")

@app.get("/")
def root():
    return {"message": "Hello CEO! AIMX is ready for duty."}