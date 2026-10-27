from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pycomm3 import LogixDriver

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

CLP_PATH = '192.168.23.143/1/3' # Lembre-se de colocar o seu IP e Slot corretos

class ComandoBomba(BaseModel):
    ligar: bool

# Nova estrutura para o Setpoint
class ComandoSetpoint(BaseModel):
    valor: float

@app.get("/api/dados")
def ler_dados():
    try:
        with LogixDriver(CLP_PATH) as plc:
            nivel = plc.read('Nivel_Tanque')
            Liga_motor1 = plc.read('Liga_motor_M1')
            # Lemos também o setpoint atual para mostrar na tela, se desejar
            resultado = plc.read('Setpoint_tanque')
            
            return {
                "sucesso": True,
                "nivel_tanque": round(nivel.value, 1) if nivel.value else 0,
                "bomba_ligada": Liga_motor1.value,
                "setpoint_atual": round(resultado.value, 1) if resultado.value else 0
            }
    except Exception as e:
        return {"sucesso": False, "erro": str(e)}

@app.post("/api/bomba")
def controlar_bomba(comando: ComandoBomba):
    try:
        with LogixDriver(CLP_PATH) as plc:
            plc.write('Liga_motor_M1', comando.ligar)
            return {"sucesso": True, "bomba_ligada": comando.ligar}
    except Exception as e:
        return {"sucesso": False, "erro": str(e)}

@app.post("/api/setpoint")
def escrever_setpoint(comando: ComandoSetpoint):
    try:
        # Imprime no terminal do uvicorn o valor que chegou da web
        print(f"\n---> Recebido da Web: {comando.valor} (Tipo: {type(comando.valor)})") 
        
        with LogixDriver(CLP_PATH) as plc:
            # Tenta escrever no CLP
            resultado = plc.write('Setpoint_tanque', comando.valor)
            print(f"---> Resposta do CLP: {resultado}")
            
            if resultado.error:
                print(f"---> ERRO DO CLP: {resultado.error}")
                return {"sucesso": False, "erro": resultado.error}
                
            return {"sucesso": True, "setpoint": comando.valor}
            
    except Exception as e:
        print(f"\n---> !!! EXCEÇÃO NO PYTHON !!!: {e}")
        return {"sucesso": False, "erro": str(e)}