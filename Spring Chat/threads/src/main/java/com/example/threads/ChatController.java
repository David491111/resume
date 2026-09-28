package com.example.threads;

import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.GetMapping;

@Controller
public class ChatController {

    @GetMapping("/")
    public String chat() {
        return "redirect:/chat.html";
    }
}