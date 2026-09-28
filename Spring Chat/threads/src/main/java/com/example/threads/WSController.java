package com.example.threads;

import lombok.AllArgsConstructor;
import org.springframework.messaging.handler.annotation.MessageMapping;
import org.springframework.messaging.simp.SimpMessagingTemplate;
import org.springframework.messaging.simp.annotation.SendToUser;
import org.springframework.stereotype.Controller;

@Controller
@AllArgsConstructor
public class WSController {
    private DB db;
    private SimpMessagingTemplate tem;
    @MessageMapping("/getMessages")
    @SendToUser("/queue/reply")
    public Iterable<Message> getMessages(){
        return db.getMessages();
    }
    @MessageMapping("/sendMessage")
    public void sendMessage(Message mes){
        db.saveMessage(mes);
        tem.convertAndSend("/topic/all", db.getMessages());
    }
}
