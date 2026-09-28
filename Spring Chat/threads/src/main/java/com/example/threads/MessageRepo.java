package com.example.threads;

import org.springframework.data.repository.CrudRepository;

import java.util.List;

public interface MessageRepo extends CrudRepository<Message,Long> {
    List<Message> findByUserName(String userName);
}
