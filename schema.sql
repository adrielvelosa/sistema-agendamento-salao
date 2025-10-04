CREATE TABLE servico (
    id INTEGER NOT NULL,
    nome VARCHAR(100) NOT NULL,
    duracao_minutos INTEGER NOT NULL,
    preco FLOAT NOT NULL,
    PRIMARY KEY (id),
    UNIQUE (nome)
);

CREATE TABLE cliente (
    id INTEGER NOT NULL,
    nome VARCHAR(100) NOT NULL,
    telefone VARCHAR(20) NOT NULL,
    PRIMARY KEY (id),
    UNIQUE (telefone)
);

CREATE TABLE usuario (
    id INTEGER NOT NULL,
    username VARCHAR(80) NOT NULL,
    password_hash VARCHAR(128),
    PRIMARY KEY (id),
    UNIQUE (username)
);

CREATE TABLE agendamento (
    id INTEGER NOT NULL,
    data_hora DATETIME NOT NULL,
    status VARCHAR(50),
    cliente_id INTEGER NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY(cliente_id) REFERENCES cliente (id)
);

CREATE TABLE agendamento_servicos (
    agendamento_id INTEGER NOT NULL,
    servico_id INTEGER NOT NULL,
    PRIMARY KEY (agendamento_id, servico_id),
    FOREIGN KEY(agendamento_id) REFERENCES agendamento (id),
    FOREIGN KEY(servico_id) REFERENCES servico (id)
);