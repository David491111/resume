package com.example.threads;

import jakarta.transaction.Transactional;
import lombok.AllArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.concurrent.locks.ReentrantLock;

@Service
@AllArgsConstructor
public class DB {
    private final MessageRepo repo;
    private final ReentrantLock lock=new ReentrantLock();
    @Transactional
    public boolean saveMessage(Message mes){
        repo.save(mes);
        return true;
    }
    public Iterable<Message> getMessages(){
        return repo.findAll();
    }
    @Transactional
    public void clearAll() {
        repo.deleteAll();
        System.out.println("All users deleted");
    }
}
