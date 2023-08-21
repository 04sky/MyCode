### 2.2.3 线程中断

```Java
public static void main(String[] args) throws InterruptedException{
    Thread t1 = new Thread(() -> {
        while(true){
            if (Thread.currentThread().isInterrupted()) {
                System.out.println("中断...");
                break;
            }
            try {
                Thread.sleep(3000);
            } catch (InterruptedException e) {
                System.out.println("Thread interruptedException");
                Thread.currentThread().interrupt();
            }
            Thread.yield();
        }
    });
    t1.start();
    Thread.sleep(2000);
    t1.interrupt();
}
```

这段代码有几个要点：

首先是t1.interrupt()会底层设置中断标志位，并不会立即停止线程执行，不同以往的stop方法

```Java
public void interrupt() {
    if (this != Thread.currentThread())
        checkAccess();

    synchronized (blockerLock) {
        Interruptible b = blocker;
        if (b != null) {
            interrupt0();           // Just to set the interrupt flag
            b.interrupt(this);
            return;
        }
    }
    interrupt0();
}

private native void interrupt0();
```

第二个是Thread.currentThread().isInterrupted()，也是实例的方法，判断当前线程的中断位是否设置，是返回True，否则返回false。

```Java
public boolean isInterrupted() {
    return isInterrupted(false);
}
/**
 * Tests if some Thread has been interrupted.  The interrupted state
 * is reset or not based on the value of ClearInterrupted that is
 * passed.
 */
private native boolean isInterrupted(boolean ClearInterrupted);
```

第三个是线程的静态方法 Thread.interrupted() ，注意这里传的是true，判断后会重置中断状态。

```Java
public static boolean interrupted() {
    return currentThread().isInterrupted(true);
}
```

第四个要点是 Thread.sleep(3000);方法，会抛出中断异常错误InterruptedException，该错误不是运行时异常，所以程序一定要处理，并且该方法捕获后（为什么要捕获？可能会做一些操作。）会将中断状态重置，所以一般后面重新设置中断标志状态。

### 2.2.4 wait()和notify()

```Java
public class CyclicBarrier {
    final static Object obj = new Object();
    static class T1 extends Thread{
        @Override
        public void run() {
            synchronized (obj){
                System.out.println("T1 start...");

                try {
                    System.out.println("T1 wait()");
                    obj.wait();
                } catch (InterruptedException e) {
                    e.printStackTrace();
                }
                System.out.println("T1 over...");
            }
        }
    }
    static class T2 extends Thread{
        @Override
        public void run() {
            synchronized (obj){
                System.out.println("T2 start...");

                System.out.println("T2 notify()");
                obj.notify();

                try {
                    System.out.println("T2 sleep()");
                    Thread.sleep(2000);
                } catch (InterruptedException e) {
                    e.printStackTrace();
                }
                System.out.println("T2 over");
            }
        }
    }
    public static void main(String[] args){
        Thread t1 = new T1();
        Thread t2 = new T2();

        t1.start();
        t2.start();
    }
}
```

这里的几个要点如下：

首先 wait() 和 notify() 方法都是object类的方法，而不是Thread类的，所有每个对象都有，但是必须存在于调用对象的监视器（也就是相同对象的synchronized语句中）中。

第二 wait() 方法会将会将当前等待的线程放入obj的等待队列中，当在其他地方使用了notify()方法会 **随机** 唤醒一个等待的线程，而 notifyAll() 会唤醒所有等待线程。

第三唤醒后得线程还是必须等待回去对象的监视器，才能继续执行。

### 2.2.4 suspend()和resume()

```
public class CyclicBarrier {

    private static Object u = new Object();

    static class ChangeThread extends Thread{
        volatile boolean suspendme = false;
        public void suspendMe(){
            suspendme = true;
        }

        public void resumeMe(){
            suspendme = false;
            synchronized (this){
                notify();
            }
        }
        @Override
        public void run() {
            while(true){
                synchronized (this){
                    try {
                        wait();
                    } catch (InterruptedException e) {
                        e.printStackTrace();
                    }
                }
                synchronized (u) {
                    System.out.println("in ChangeThread");
                }
                Thread.yield();
            }

        }
    }
    public static class ReadObjectThread extends Thread{
        @Override
        public void run() {
            while(true){
                synchronized (u){
                    System.out.println("in readObjectThread");
                }
                Thread.yield();
            }
        }
    }
    public static void main(String[] args) throws InterruptedException{
        ChangeThread t1 = new ChangeThread();
        ReadObjectThread t2 = new ReadObjectThread();
        t1.start();
        t2.start();
        Thread.sleep(1000);
        t1.suspendMe();
        System.out.println("suspend t1 2 sec");
        Thread.sleep(2000);
        System.out.println("resume t1");
        t1.resumeMe();
    }
}
```

 要点：这两个方法被放弃使用，因为它会挂起一个线程，并不会释放掉该线程所占用的资源，其他请求该资源的线程都会阻塞，若resume()在这之前使用了，会造成类似死锁的情况。并且挂起的线程的状态为RUNNABLE，可能会误判线程状态。

### 2.2.4 join()和yield()

```
public class CyclicBarrier {
    public volatile static int i = 0;
    static class Addthead extends Thread{
        @Override
        public void run() {
            for (;i < 10000000; i++) {

            }
        }
    }
    public static void main(String[] args) throws InterruptedException{
        Addthead t1 = new Addthead();
        t1.start();
        t1.join();
        System.out.println(i);
    }
}
```

join方法要点：本质是是通过调用wait()方法，让调用线程在被等待线程对象上进行等待，等到被等待执行结束之前，调用notifyAll唤醒所以等待的线程。

yield()方法要点：它会让出cpu资源，但在让出后，还是会**参与到竞争CPU资源**。

### 2.4 线程组

```Java
public class CyclicBarrier implements Runnable{
    public static void main(String[] args) {
        ThreadGroup tg = new ThreadGroup("PrintGroup");
        Thread t1 = new Thread(tg, new CyclicBarrier(), "t1");
        Thread t2 = new Thread(tg, new CyclicBarrier(), "t2");
        t1.start();
        t2.start();
        System.out.println(tg.activeCount());
        tg.list();
    }

    @Override
    public void run() {
        String groupAndName = Thread.currentThread().getThreadGroup().getName() + "-"
                + Thread.currentThread().getName();
        while(true){
            System.out.println("i am " + groupAndName);
            try {
                TimeUnit.SECONDS.sleep(3);
            } catch (InterruptedException e) {
                e.printStackTrace();
            }
        }
    }
}
```

注意：tg.stop() 方法也有类似线程stop()方法的错误。

### 2.5 守护线程

```Java
public class CyclicBarrier extends Thread{
    public static void main(String[] args) {
        CyclicBarrier main = new CyclicBarrier();
        main.setDaemon(true);
        main.start();

        try {
            TimeUnit.SECONDS.sleep(2);
        } catch (InterruptedException e) {
            e.printStackTrace();
        }

    }

    @Override
    public void run() {
        while(true){
            System.out.println("i am running.");
            try {
                TimeUnit.SECONDS.sleep(1);
            } catch (InterruptedException e) {
                e.printStackTrace();
            }
        }

    }
}
```

注意点：

​	1）当只有守护线程在运行时，Java虚拟机就会退出。

​	2）setDaemon(true) 方法应在 start() 方法之前执行，若在之后，会报错：

```JVM
Exception in thread "main" java.lang.IllegalThreadStateException
```

​		并且将当做普通线程执行。

### 2.6 线程优先级

```Java
public class CyclicBarrier{
    static class LowPriority extends Thread{
        static int count = 0;
        @Override
        public void run() {
            while(true){
                synchronized (CyclicBarrier.class){
                    count++;
                    if (count>=10000000) {
                        break;
                    }
                }
            }
            System.out.println("low finish.");
        }
    }
    static class HighPriority extends Thread{
        static int count = 0;
        @Override
        public void run() {
            while(true){
                synchronized (CyclicBarrier.class){
                    count++;
                    if (count>=10000000) {
                        break;
                    }
                }
            }
            System.out.println("high finish.");
        }
    }
    public static void main(String[] args) {
        LowPriority lowPriority = new LowPriority();
        HighPriority highPriority = new HighPriority();
        lowPriority.setPriority(Thread.MIN_PRIORITY);
        highPriority.setPriority(Thread.MAX_PRIORITY);
        lowPriority.start();
        highPriority.start();

    }
}
```

注意：

​	1）高优先级的线程只是抢到资源的概率高，不一定一定先于低优先级。

​	2）低优先级可能出现“饿死”情况，对一些场合需要在应用层解决。

### 2.7 ArrayList的并发下错误

```Java
public class CyclicBarrier extends Thread{
    static ArrayList<Integer> arrayList = new ArrayList<>();
    @Override
    public void run() {
        for (int i=0; i<100000;i++) {
            arrayList.add(i);
        }
    }

    public static void main(String[] args) throws InterruptedException{
        CyclicBarrier main1 = new CyclicBarrier();
        CyclicBarrier main2 = new CyclicBarrier();
        main1.start();
        main2.start();
        main1.join();main2.join();
        System.out.println(CyclicBarrier.arrayList.size());
    }
}
```

注意：程序可能会出现以下三种情况

​	1）正常运行输出200000，这是可能的。

​	2）报错，出现内部一致性被破坏，另一个线程访问到了内部不一致的状态。

```JVM
Exception in thread "Thread-1" java.lang.ArrayIndexOutOfBoundsException: 10
```

​	3）出现了一个小于200000的数，但没有报错。这是因为多个线程同时在一个地方赋值。

### 2.7 HashMap在并发下错误

```Java
public class CyclicBarrier{
    static HashMap<String, String> hashMap = new HashMap<>();

    public static class AddClass implements Runnable{
        int start = 0;
        public AddClass(int start){
            this.start = start;
        }
        @Override
        public void run() {
            for (int i=start; i<100000; i+=2) {
                hashMap.put(Integer.toString(i), Integer.toBinaryString(i));
            }
        }
    }

    public static void main(String[] args) throws InterruptedException{
        Thread t1 = new Thread(new AddClass(0));
        Thread t2 = new Thread(new AddClass(1));
        t1.start();
        t2.start();
        t1.join();
        t2.join();
        System.out.println(hashMap.size());
    }
}
```

注意：在JDK7中可能出现3种情况。

​	1）正常结束。

​	2）正常结束，但是输出size比预期的小，出现了操作被覆盖的情况。

​	3）程序永远无法结束，可能出现了链表成环的情况。

​		Java8进行修正，但是还有问题，比如类型转换异常。

```Java
java.lang.ClassCastException: java.util.HashMap$Node cannot be cast to java.util.HashMap$TreeNode
```

## 3  JDK并发包

### 3.1 可重入锁

注意：

​	（1）当unlock() 比 lock() 多时，会抛出 java.lang.IllegalMonitorStateException 异常。

​	（2）当lock() 比 unlock() 多时，会一直阻塞。

​	（3）当condition.signal未包含于reentrantLock.lock()和reentrantLock.unlock()中，会抛出  java.lang.IllegalMonitorStateException 异常。

### 3.2 CyclicBarrier

注意：

​	（1）可能会出现两种异常，第一种是InteruptException，另一个是BrokenBarrierException，比如当其中某个线程中断，这个线程抛出InteruptException，其他9个是BrokenBarrierException，被

等待在当前CyclicBarrier上的线程抛出