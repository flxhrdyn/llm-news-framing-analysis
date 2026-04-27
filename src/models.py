from typing import List, Optional
from pydantic import BaseModel, Field


class FramingModel(BaseModel):
    """Skema untuk analisis framing Robert Entman."""
    problem_definition: str = Field(description="Apa yang dianggap sebagai masalah utama dalam narasi?")
    causal_interpretation: str = Field(description="Siapa atau apa yang dianggap sebagai penyebab atau aktor di balik isu tersebut?")
    moral_evaluation: str = Field(description="Bagaimana penilaian etika atau 'pahlawan vs penjahat' diterapkan?")
    treatment_recommendation: str = Field(description="Apa solusi yang ditawarkan atau diimplikasikan oleh media?")


class AnalysisResultModel(BaseModel):
    """Skema lengkap hasil analisis artikel berita."""
    framing: FramingModel
    actors: List[str] = Field(description="Daftar 3-5 aktor utama (tokoh, kelompok, atau lembaga).")
    sentiment: str = Field(description="Sentimen keseluruhan (Positif, Negatif, atau Netral).")
    sentiment_reason: str = Field(description="Alasan singkat mengapa sentimen tersebut dipilih.")
