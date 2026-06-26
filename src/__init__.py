"""Atlas de Potencial Solar do Brasil — pacote de ingestão, limpeza e agregação espacial.

Módulos:
    config        — caminhos, URLs das fontes e constantes de domínio.
    download      — baixar/descompactar os dados brutos (INPE, ANEEL).
    ingest_inpe   — carregar a grade de irradiação como pontos.
    ingest_aneel  — agregar potência FV instalada por município.
    ingest_ibge   — malhas municipais/estaduais e população.
    aggregate     — junção espacial + cruzamento recurso × uso + índice de oportunidade.
"""
__version__ = "0.1.0"
