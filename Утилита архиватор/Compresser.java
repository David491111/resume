import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.IOException;
import java.lang.reflect.AnnotatedArrayType;
import java.nio.file.Files;
import java.nio.file.OpenOption;
import java.nio.file.Path;
import java.util.*;

import static java.nio.file.StandardOpenOption.*;

public class Compresser{
    public static void main(String[] args) throws IOException {
        if (args.length<1 && args.length>2){
            IO.println("Write file name and -d to decompress");
            return ;
        }
        else if(args.length==1){
            Path fileName= Path.of(args[0]);
            HashMap<Character,Integer> regularity=new HashMap<>();
            createRegularity(fileName, regularity);
            regularity.put('\0',0);
            System.out.println("Regularity table created");
            HashMap<Character,String> codeTable=new HashMap<>();
            ArrayList<String> sortedChars=new ArrayList<>(regularity.keySet().stream().map(Object::toString).toList());
            Collections.sort(sortedChars,(e1,e2)->regularity.get(e2.toCharArray()[0])-regularity.get(e1.toCharArray()[0]));
//            printMap(regularity);
//            printList(sortedChars);
            createCodeTable(sortedChars,codeTable,regularity);
            System.out.println("Code table created");
            //printMap(codeTable);
            StringBuffer ans=new StringBuffer();
            String terminator=codeTable.get('\0');
            writeTable(ans,regularity);
            File fl=new File(args[0]);
            String fileName2=fl.getAbsolutePath()+".dddd";
            Files.writeString(Path.of(fileName2), ans, CREATE, TRUNCATE_EXISTING);
            System.out.println("Head table is done");
            byte[] text = getCompressedText(codeTable,terminator,fileName).stream()
                    .mapToInt(Byte::byteValue)
                    .collect(ByteArrayOutputStream::new,
                            ByteArrayOutputStream::write,
                            (baos1, baos2) -> baos1.write(baos2.toByteArray(), 0, baos2.size()))
                    .toByteArray();;
            Files.write(Path.of(fileName2), text, APPEND);
            System.out.println("File compressed");
        }
        else if(args.length==2 && args[1].equals("-d")){
            String fileName=args[0];
            String[] dec=fileName.split("\\.");
            if(!dec[dec.length-1].equals("dddd")){
                System.out.println("Enter correct file");
                return;
            }
            byte[] compressedText=Files.readAllBytes(Path.of(fileName));
            int[] i={0};
            int tableLen=getTableLength(i,compressedText);
            //IO.println(tableLen+" "+i[0]);
            HashMap<Character, Integer> regularity=new HashMap<>();
            getRegularityFromComp(regularity,compressedText,tableLen,i);
            //printMap(regularity);
            HashMap<Character,String> codeTable=new HashMap<>();
            ArrayList<String> sortedChars=new ArrayList<>(regularity.keySet().stream().map(Object::toString).toList());
            Collections.sort(sortedChars,(e1,e2)->regularity.get(e2.toCharArray()[0])-regularity.get(e1.toCharArray()[0]));
            createCodeTable(sortedChars, codeTable,regularity);
            //printMap(codeTable);
            HashMap<String,Character> reversedCodeTable=reverseMap(codeTable);
            //printMap(reversedCodeTable);
            StringBuffer text=new StringBuffer();
            decompess(text,compressedText,reversedCodeTable,i);
            //IO.println(text);
            String fileName2=fileName.substring(0,fileName.length()-5);
            Files.writeString(Path.of(fileName2),text.toString());
            IO.println("File decompressed");
        }
    }



    static void createRegularity(Path fileName, HashMap<Character, Integer> regularity) throws IOException {
        for(char ch : Files.readString(fileName).toCharArray()) {
            regularity.put(ch, regularity.getOrDefault(ch, 0) + 1);
        }
    }
    static <T,K>void printMap(Map<T, K> map) {
        for(Map.Entry<T,K> entry: map.entrySet()){
            System.out.println(entry.getKey().toString()+": "+entry.getValue().toString());
        }
        System.out.println();
    }
    static <T>void printList(List<T> list) {
        for(T el: list){
            System.out.println(el);
        }
        System.out.println();
    }
    static void createCodeTable(List<String> nodes, HashMap<Character,String> codeTable, HashMap<Character,Integer> regularity){
        while(nodes.size()>1){
            String a= nodes.get(nodes.size()-2);
            String b= nodes.get(nodes.size()-1);
            for(char el : a.toCharArray()){
                codeTable.put(el, "0"+codeTable.getOrDefault(el,""));
            }
            for(char el : b.toCharArray()){
                codeTable.put(el, "1"+codeTable.getOrDefault(el,""));
            }
            nodes.remove(a);
            nodes.remove(b);
            nodes.add(a+b);
            Collections.sort(nodes,(String n1,String n2)-> countRegInNode(n2,regularity)-countRegInNode(n1,regularity));
        }
    }
    static int countRegInNode(String node, HashMap<Character,Integer> regularity){
        int reg=0;
        for(char el : node.toCharArray()){
            reg+=regularity.get(el);
        }
        return reg;
    }
    static String findTerminator(Collection<String> codes){
        int len=0;
        for(String code : codes){
            if(code.length()>len){
                len=code.length();
            }
        }
        return "1".repeat(len);
    }
    static void writeTable(StringBuffer ans, HashMap<Character,Integer> regularity){
        ans.append(""+regularity.size()+" ");
        for(Map.Entry<Character,Integer> entry:regularity.entrySet()){
            ans.append(""+entry.getKey()+entry.getValue()+" ");
        }
    }
    static ArrayList<Byte> getCompressedText(HashMap<Character,String> codeTable, String terminator, Path fileName) throws IOException {
        ArrayList<Byte> text=new ArrayList<>();
        int i=0;
        for(char ch:Files.readString(fileName).toCharArray()){
            String code=codeTable.get((char)ch);
            for(int j=0; j<code.length();j++,i++){
                if(text.size()<=i/8){
                    text.add((byte)0);
                }
                text.set(i/8, (byte) ((text.get(i/8)<<1)|(code.charAt(j)-'0')));
            }
        }
        int j=0;
        for(; j<terminator.length();j++){
            if(text.size()<=(i+j)/8){
                text.add((byte)0);
            }
            text.set((i+j)/8, (byte) ((text.get((i+j)/8)<<1)|(terminator.charAt(j)-'0')));
        }
        for (;(i+j)%8!=0; j++){
            text.set((i+j)/8, (byte) ((text.get((i+j)/8)<<1)|(0)));
        }
        return text;
    }

    static int getTableLength(int[] i, byte[] text){
        while(text[i[0]]!=' '){
            i[0]++;
        }
        String len="";
        for(int j=0; j<i[0]; j++){
            len+=(char)text[j];
        }
        i[0]++;
        return Integer.parseInt(len);
    }
    static void getRegularityFromComp(HashMap<Character,Integer> regularity,byte[] text,int len, int[] i){
        String val="";
        for(int j=0; j<len;j++){
            char key;
            if((text[i[0]]&224)==192){
                byte[] buf={text[i[0]],text[i[0]+1]};
                i[0]++;
                key=new String(buf).charAt(0);
            }
            else if((text[i[0]]&240)==224){
                byte[] buf={text[i[0]],text[i[0]+1],text[i[0]+2]};
                i[0]+=2;
                key=new String(buf).charAt(0);
                //IO.println(""+key+" "+(key+0)+" "+new String(buf).length()); // для эксперимента
            }
            else {
                key = (char) text[i[0]];
            }
            i[0]++;
            val="";
            while(text[i[0]]!=' '){
                val+=(char)text[i[0]];
                i[0]++;
            }
            i[0]++;
            regularity.put(key,Integer.parseInt(val));
        }
    }
    static <T,K> HashMap<K,T> reverseMap(Map<T,K> originalMap){
        HashMap<K,T> reversedMap=new HashMap<>();
        for(Map.Entry entry: originalMap.entrySet()){
            reversedMap.put((K) entry.getValue(), (T) entry.getKey());
        }
        return reversedMap;
    }
    static void decompess(StringBuffer decompressedText, byte[] text, HashMap<String,Character> codeTable, int[] i){
        int k=i[0]*8;
        StringBuffer code=new StringBuffer();
        while(k/8<text.length){
            code.append((text[k/8]&Math.powExact(2,7-k%8))>0 ? "1":"0");
            k++;
            if (codeTable.containsKey(code.toString())){
                if(codeTable.get(code.toString())=='\0'){
                    break;
                }
                decompressedText.append(codeTable.get(code.toString()));
                code=new StringBuffer();
            }
        }
    }
}