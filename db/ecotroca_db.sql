CREATE SCHEMA IF NOT EXISTS ecotroca DEFAULT CHARACTER SET utf8 ;
USE ecotroca ;

-- -----------------------------------------------------
-- Table ecotroca.USUARIO
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS ecotroca.USUARIO (
    id_usuario INT NOT NULL AUTO_INCREMENT,
    nome_usuario VARCHAR(150) NOT NULL,
    cpf VARCHAR(14) NULL,
    telefone VARCHAR(14) NOT NULL,
    email VARCHAR(150) NOT NULL,
    senha VARCHAR(250) NOT NULL,
    data_cadastro DATETIME NOT NULL,
    data_nascimento DATE NOT NULL,
    PRIMARY KEY (id_usuario),
    UNIQUE INDEX email_UNIQUE (email ASC),
    UNIQUE INDEX cpf_UNIQUE (cpf ASC)
)  ENGINE=INNODB;

-- -----------------------------------------------------
-- Table ecotroca.ENDERECO_USUARIO
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS ecotroca.ENDERECO_USUARIO (
    id_endereco INT NOT NULL AUTO_INCREMENT,
    cep VARCHAR(9) NOT NULL,
    bairro VARCHAR(80) NOT NULL,
    rua VARCHAR(80) NOT NULL,
    numero VARCHAR(10) NOT NULL,
    complemento VARCHAR(150) NULL,
    cidade VARCHAR(80) NOT NULL,
    estado VARCHAR(50) NOT NULL,
    id_usuario INT NOT NULL,
    PRIMARY KEY (id_endereco),
    INDEX fk_ENDERECO_USUARIO1_idx (id_usuario ASC),
    CONSTRAINT fk_ENDERECO_USUARIO1 FOREIGN KEY (id_usuario)
        REFERENCES ecotroca.USUARIO (id_usuario)
        ON DELETE NO ACTION ON UPDATE NO ACTION
)  ENGINE=INNODB;

-- -----------------------------------------------------
-- Table ecotroca.CATEGORIA
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS ecotroca.CATEGORIA (
    id_categoria INT NOT NULL AUTO_INCREMENT,
    nome_categoria VARCHAR(20) NOT NULL,
    descricao VARCHAR(80) NOT NULL,
    PRIMARY KEY (id_categoria)
)  ENGINE=INNODB;

-- -----------------------------------------------------
-- Table ecotroca.PRODUTO
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS ecotroca.PRODUTO (
    id_produto INT NOT NULL AUTO_INCREMENT,
    nome_produto VARCHAR(80) NOT NULL,
    descricao VARCHAR(200) NOT NULL,
    status ENUM('NOVO', 'USADO') NOT NULL,
    data_cadastro DATE NOT NULL,
    quantidade INT NOT NULL,
    valor DECIMAL(10 , 2 ) NULL,
    id_usuario INT NOT NULL,
    id_categoria INT NOT NULL,
    PRIMARY KEY (id_produto),
    INDEX fk_PRODUTO_USUARIO_idx (id_usuario ASC),
    INDEX fk_PRODUTO_CATEGORIA_idx (id_categoria ASC),
    CONSTRAINT fk_PRODUTO_USUARIO FOREIGN KEY (id_usuario)
        REFERENCES ecotroca.USUARIO (id_usuario)
        ON DELETE NO ACTION ON UPDATE NO ACTION,
    CONSTRAINT fk_PRODUTO_CATEGORIA FOREIGN KEY (id_categoria)
        REFERENCES ecotroca.CATEGORIA (id_categoria)
        ON DELETE NO ACTION ON UPDATE NO ACTION
)  ENGINE=INNODB;

-- -----------------------------------------------------
-- Table ecotroca.IMAGEM
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS ecotroca.IMAGEM (
    id_imagem INT NOT NULL AUTO_INCREMENT,
    url_imagem VARCHAR(200) NOT NULL,
    descricao_imagem VARCHAR(100) NULL,
    id_produto INT NOT NULL,
    PRIMARY KEY (id_imagem),
    INDEX fk_IMAGEM_PRODUTO1_idx (id_produto ASC),
    CONSTRAINT fk_IMAGEM_PRODUTO1 FOREIGN KEY (id_produto)
        REFERENCES ecotroca.PRODUTO (id_produto)
        ON DELETE NO ACTION ON UPDATE NO ACTION
)  ENGINE=INNODB;

-- -----------------------------------------------------
-- Table ecotroca.TRANSACAO
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS ecotroca.TRANSACAO (
    id_transacao INT NOT NULL AUTO_INCREMENT,
    data_transacao DATE NOT NULL,
    PRIMARY KEY (id_transacao)
)  ENGINE=INNODB;

-- -----------------------------------------------------
-- Table ecotroca.SOLICITACAO
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS ecotroca.SOLICITACAO (
    id_solicitacao INT NOT NULL AUTO_INCREMENT,
    status ENUM('PROCESSANDO', 'PENDENTE', 'APROVADA', 'RECUSADA', 'CANCELADA') NOT NULL,
    data_solicitacao DATETIME NOT NULL,
    id_usuario_solicitante INT NOT NULL,
    id_produto_desejado INT NULL, 
    id_transacao INT NULL,
    PRIMARY KEY (id_solicitacao),
    INDEX fk_SOLICITACAO_USUARIO1_idx (id_usuario_solicitante ASC),
    INDEX fk_SOLICITACAO_PRODUTO_DESEJADO_idx (id_produto_desejado ASC),
    INDEX fk_SOLICITACAO_TRANSACAO_idx (id_transacao ASC),
    CONSTRAINT fk_SOLICITACAO_USUARIO1 FOREIGN KEY (id_usuario_solicitante)
        REFERENCES ecotroca.USUARIO (id_usuario)
        ON DELETE NO ACTION ON UPDATE NO ACTION,
    CONSTRAINT fk_SOLICITACAO_PRODUTO_DESEJADO FOREIGN KEY (id_produto_desejado)
        REFERENCES ecotroca.PRODUTO (id_produto)
        ON DELETE SET NULL ON UPDATE NO ACTION,
    CONSTRAINT fk_SOLICITACAO_TRANSACAO FOREIGN KEY (id_transacao)
        REFERENCES ecotroca.TRANSACAO (id_transacao)
        ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=INNODB;

-- -----------------------------------------------------
-- Table ecotroca.MENSAGEM
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS ecotroca.MENSAGEM (
    id_mensagem INT NOT NULL AUTO_INCREMENT,
    conteudo_mensagem VARCHAR(100) NOT NULL,
    data_envio DATE NOT NULL,
    id_usuario INT NOT NULL,
    id_solicitacao INT NOT NULL,
    PRIMARY KEY (id_mensagem),
    INDEX fk_MENSAGEM_USUARIO1_idx (id_usuario ASC),
    INDEX fk_MENSAGEM_SOLICITACAO1_idx (id_solicitacao ASC),
    CONSTRAINT fk_MENSAGEM_USUARIO1 FOREIGN KEY (id_usuario)
        REFERENCES ecotroca.USUARIO (id_usuario)
        ON DELETE NO ACTION ON UPDATE NO ACTION,
    CONSTRAINT fk_MENSAGEM_SOLICITACAO1 FOREIGN KEY (id_solicitacao)
        REFERENCES ecotroca.SOLICITACAO (id_solicitacao)
        ON DELETE NO ACTION ON UPDATE NO ACTION
)  ENGINE=INNODB;

-- -----------------------------------------------------
-- Table ecotroca.SOLICITACAO_PRODUTO_OFERTADO
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS ecotroca.SOLICITACAO_PRODUTO_OFERTADO (
    id_solicitacao INT NOT NULL,
    id_produto INT NOT NULL,
    PRIMARY KEY (id_solicitacao, id_produto),
    CONSTRAINT fk_SOLICITACAO_PRODUTO_SOLICITACAO
        FOREIGN KEY (id_solicitacao) REFERENCES ecotroca.SOLICITACAO(id_solicitacao)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_SOLICITACAO_PRODUTO_PRODUTO
        FOREIGN KEY (id_produto) REFERENCES ecotroca.PRODUTO(id_produto)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;

-- -----------------------------------------------------
-- Inserts iniciais
-- -----------------------------------------------------
INSERT INTO ecotroca.categoria (nome_categoria, descricao) VALUES
('TROCA', 'Produtos disponíveis para troca'),
('DOAÇÃO', 'Produtos disponíveis para doação');