from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


# clase para la configuracion de la aplicacion, lee las variables de entorno y las valida
class Configuracion(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APPNombre: str
    APIVersion: str
    Entorno: str

    Host: str
    Puerto: int

    JWTClaveSecreta: str
    JWTAlgoritmo: Literal["HS256"]
    JWTMinutosExpiracion: int

    BaseDatosHost: str
    BaseDatosPuerto: int
    BaseDatosNombre: str
    BaseDatosUsuario: str
    BaseDatosPassword: str

    @property
    def urlBaseDatos(self) -> str:
        return (
            f"postgresql+psycopg://{self.BaseDatosUsuario}:"
            f"{self.BaseDatosPassword}@{self.BaseDatosHost}:"
            f"{self.BaseDatosPuerto}/{self.BaseDatosNombre}"
        )


configuracion = Configuracion()
