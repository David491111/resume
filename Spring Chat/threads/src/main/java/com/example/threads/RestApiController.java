package com.example.threads;

import lombok.AllArgsConstructor;
import org.springframework.messaging.simp.SimpMessagingTemplate;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/rest")
@AllArgsConstructor
public class RestApiController {
    private DB db;
    private SimpMessagingTemplate tem;
    @RequestMapping("/threads")
    public String threadCount(){
        return 	Thread.activeCount()+" threads is active";
    }
    @RequestMapping("/chat")
    public Iterable<Message> getChat(){
        return db.getMessages();
    }
    @PostMapping("/sendMessage")
    public boolean sendMessage(@RequestBody Message mes){
        boolean f=db.saveMessage(mes);
        tem.convertAndSend("/topic/all", db.getMessages());
        return f;
    }
    @RequestMapping("/clear")
    public void clearUsers() {
        db.clearAll();
        tem.convertAndSend("/topic/all", db.getMessages());
    }
}
