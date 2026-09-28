package com.example.threads;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
public class ThreadsApplication {

	public static void main(String[] args) {
		SpringApplication.run(ThreadsApplication.class, args);
        System.out.println("App started");
	}

}
