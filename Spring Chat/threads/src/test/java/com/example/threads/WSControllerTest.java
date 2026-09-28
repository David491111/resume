package com.example.threads;

import org.apache.catalina.core.ApplicationContext;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.Mockito;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.webtestclient.autoconfigure.AutoConfigureWebTestClient;
import org.springframework.messaging.simp.SimpMessagingTemplate;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.reactive.server.WebTestClient;

import java.util.Iterator;
import java.util.List;

import static org.junit.jupiter.api.Assertions.*;

@ExtendWith(MockitoExtension.class)

class WSControllerTest {

    @Mock
    private DB db;

    @Mock
    private SimpMessagingTemplate messagingTemplate;

    private Message m1, m2;

    @InjectMocks
    private WSController controller;

    @BeforeEach
    void setUp() {
        m1=new Message(1L,"me","hi");
        m2=new Message(2L,"you","hello");
        Mockito.when(db.getMessages()).thenReturn(List.of(m1,m2));
    }

    @AfterEach
    void tearDown() {
    }

    @Test
    void getMessages() {
        final Iterable<Message> mes=controller.getMessages();
        assert mes.equals(db.getMessages());
    }
}