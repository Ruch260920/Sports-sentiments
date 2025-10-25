#!/usr/bin/env python3
"""
Scheduler script for managing scraping tasks for multiple entities

This script provides functionality to:
- Register new entities for scraping
- Schedule scraping tasks for multiple entities
- Manage scraping intervals and configurations
- Monitor task status and results
"""

import os
import sys
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class ScrapingScheduler:
    """Scheduler for managing scraping tasks for multiple entities"""
    
    def __init__(self):
        self.entities_file = "entities_config.json"
        self.entities = self.load_entities()
        
    def load_entities(self) -> Dict:
        """Load entities configuration from file"""
        if os.path.exists(self.entities_file):
            try:
                with open(self.entities_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading entities config: {e}")
                return {}
        return {}
    
    def save_entities(self):
        """Save entities configuration to file"""
        try:
            with open(self.entities_file, 'w') as f:
                json.dump(self.entities, f, indent=2)
        except Exception as e:
            print(f"Error saving entities config: {e}")
    
    def add_entity(self, name: str, description: str = "", 
                   scraping_interval_hours: int = 6, max_articles: int = 50,
                   is_active: bool = True) -> bool:
        """
        Add a new entity for scraping
        
        Args:
            name (str): Entity name
            description (str): Entity description
            scraping_interval_hours (int): Hours between scraping runs
            max_articles (int): Maximum articles to scrape per run
            is_active (bool): Whether entity is active for scraping
            
        Returns:
            bool: True if entity was added successfully
        """
        try:
            # Add to database
            from models.database import SessionLocal
            from models.models import Entity
            
            db = SessionLocal()
            try:
                # Check if entity already exists
                existing = db.query(Entity).filter(Entity.name == name).first()
                if existing:
                    print(f"Entity '{name}' already exists in database")
                    return False
                
                # Create new entity
                entity = Entity(
                    name=name,
                    description=description,
                    is_active=is_active
                )
                db.add(entity)
                db.commit()
                db.refresh(entity)
                
                # Add to configuration
                self.entities[name] = {
                    "id": entity.id,
                    "description": description,
                    "scraping_interval_hours": scraping_interval_hours,
                    "max_articles": max_articles,
                    "is_active": is_active,
                    "last_scraped": None,
                    "created_at": datetime.now().isoformat()
                }
                
                self.save_entities()
                print(f"✓ Added entity '{name}' successfully")
                return True
                
            finally:
                db.close()
                
        except Exception as e:
            print(f"✗ Error adding entity '{name}': {e}")
            return False
    
    def remove_entity(self, name: str) -> bool:
        """
        Remove an entity from scraping
        
        Args:
            name (str): Entity name to remove
            
        Returns:
            bool: True if entity was removed successfully
        """
        try:
            # Update database
            from models.database import SessionLocal
            from models.models import Entity
            
            db = SessionLocal()
            try:
                entity = db.query(Entity).filter(Entity.name == name).first()
                if entity:
                    entity.is_active = False
                    db.commit()
                
                # Remove from configuration
                if name in self.entities:
                    del self.entities[name]
                    self.save_entities()
                
                print(f"✓ Removed entity '{name}' successfully")
                return True
                
            finally:
                db.close()
                
        except Exception as e:
            print(f"✗ Error removing entity '{name}': {e}")
            return False
    
    def update_entity_config(self, name: str, **kwargs) -> bool:
        """
        Update entity configuration
        
        Args:
            name (str): Entity name
            **kwargs: Configuration parameters to update
            
        Returns:
            bool: True if configuration was updated successfully
        """
        if name not in self.entities:
            print(f"Entity '{name}' not found in configuration")
            return False
        
        try:
            # Update configuration
            for key, value in kwargs.items():
                if key in self.entities[name]:
                    self.entities[name][key] = value
            
            self.save_entities()
            print(f"✓ Updated configuration for entity '{name}'")
            return True
            
        except Exception as e:
            print(f"✗ Error updating entity '{name}': {e}")
            return False
    
    def list_entities(self) -> List[Dict]:
        """List all configured entities"""
        entities_list = []
        
        for name, config in self.entities.items():
            entity_info = {
                "name": name,
                "description": config.get("description", ""),
                "is_active": config.get("is_active", True),
                "scraping_interval_hours": config.get("scraping_interval_hours", 6),
                "max_articles": config.get("max_articles", 50),
                "last_scraped": config.get("last_scraped"),
                "created_at": config.get("created_at")
            }
            entities_list.append(entity_info)
        
        return entities_list
    
    def run_scraping_for_entity(self, name: str) -> bool:
        """
        Run scraping for a specific entity
        
        Args:
            name (str): Entity name to scrape
            
        Returns:
            bool: True if scraping was successful
        """
        if name not in self.entities:
            print(f"Entity '{name}' not found in configuration")
            return False
        
        try:
            from tasks.scraping_tasks import scrape_entity_articles
            
            config = self.entities[name]
            
            # Run scraping task
            result = scrape_entity_articles.delay(
                name,
                max_articles=config.get("max_articles", 50),
                days_back=7
            )
            
            # Update last scraped time
            self.entities[name]["last_scraped"] = datetime.now().isoformat()
            self.save_entities()
            
            print(f"✓ Started scraping for '{name}' (Task ID: {result.id})")
            return True
            
        except Exception as e:
            print(f"✗ Error running scraping for '{name}': {e}")
            return False
    
    def run_scraping_for_all_active(self) -> Dict:
        """
        Run scraping for all active entities
        
        Returns:
            Dict: Results for each entity
        """
        results = {}
        
        for name, config in self.entities.items():
            if config.get("is_active", True):
                success = self.run_scraping_for_entity(name)
                results[name] = {
                    "success": success,
                    "timestamp": datetime.now().isoformat()
                }
        
        return results
    
    def check_scheduled_scraping(self) -> List[str]:
        """
        Check which entities need to be scraped based on their schedule
        
        Returns:
            List[str]: Names of entities that need scraping
        """
        entities_to_scrape = []
        
        for name, config in self.entities.items():
            if not config.get("is_active", True):
                continue
            
            last_scraped = config.get("last_scraped")
            interval_hours = config.get("scraping_interval_hours", 6)
            
            if not last_scraped:
                # Never scraped before
                entities_to_scrape.append(name)
                continue
            
            # Check if enough time has passed
            last_scraped_dt = datetime.fromisoformat(last_scraped)
            next_scrape_time = last_scraped_dt + timedelta(hours=interval_hours)
            
            if datetime.now() >= next_scrape_time:
                entities_to_scrape.append(name)
        
        return entities_to_scrape
    
    def get_entity_stats(self, name: str) -> Dict:
        """
        Get statistics for a specific entity
        
        Args:
            name (str): Entity name
            
        Returns:
            Dict: Entity statistics
        """
        try:
            from models.database import SessionLocal
            from models.models import Entity, Article
            
            db = SessionLocal()
            
            entity = db.query(Entity).filter(Entity.name == name).first()
            if not entity:
                return {"error": "Entity not found"}
            
            # Get article counts
            total_articles = db.query(Article).filter(Article.entity_id == entity.id).count()
            
            # Recent articles (last 7 days)
            week_ago = datetime.now() - timedelta(days=7)
            recent_articles = db.query(Article).filter(
                Article.entity_id == entity.id,
                Article.scraped_date >= week_ago
            ).count()
            
            # Sentiment distribution
            sentiment_stats = db.query(Article.sentiment_label).filter(
                Article.entity_id == entity.id,
                Article.sentiment_label.isnot(None)
            ).all()
            
            sentiment_counts = {}
            for label in sentiment_stats:
                label = label[0] if label[0] else 'neutral'
                sentiment_counts[label] = sentiment_counts.get(label, 0) + 1
            
            db.close()
            
            return {
                "name": name,
                "total_articles": total_articles,
                "recent_articles": recent_articles,
                "sentiment_distribution": sentiment_counts,
                "config": self.entities.get(name, {})
            }
            
        except Exception as e:
            return {"error": str(e)}

def main():
    """Main function for command line interface"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Scraping Scheduler")
    parser.add_argument('command', choices=['add', 'remove', 'list', 'update', 'scrape', 'scrape-all', 'check', 'stats'],
                       help='Command to run')
    parser.add_argument('--name', help='Entity name')
    parser.add_argument('--description', help='Entity description')
    parser.add_argument('--interval', type=int, default=6, help='Scraping interval in hours')
    parser.add_argument('--max-articles', type=int, default=50, help='Maximum articles per scrape')
    parser.add_argument('--active', action='store_true', help='Set entity as active')
    
    args = parser.parse_args()
    
    scheduler = ScrapingScheduler()
    
    if args.command == 'add':
        if not args.name:
            print("Error: --name is required for add command")
            sys.exit(1)
        
        success = scheduler.add_entity(
            name=args.name,
            description=args.description or "",
            scraping_interval_hours=args.interval,
            max_articles=args.max_articles,
            is_active=args.active
        )
        
        if not success:
            sys.exit(1)
    
    elif args.command == 'remove':
        if not args.name:
            print("Error: --name is required for remove command")
            sys.exit(1)
        
        success = scheduler.remove_entity(args.name)
        if not success:
            sys.exit(1)
    
    elif args.command == 'list':
        entities = scheduler.list_entities()
        print("Configured Entities:")
        print("=" * 80)
        
        for entity in entities:
            status = "✓ Active" if entity["is_active"] else "✗ Inactive"
            print(f"{entity['name']} - {status}")
            print(f"  Description: {entity['description']}")
            print(f"  Interval: {entity['scraping_interval_hours']} hours")
            print(f"  Max Articles: {entity['max_articles']}")
            print(f"  Last Scraped: {entity['last_scraped'] or 'Never'}")
            print()
    
    elif args.command == 'update':
        if not args.name:
            print("Error: --name is required for update command")
            sys.exit(1)
        
        kwargs = {}
        if args.description:
            kwargs["description"] = args.description
        if args.interval:
            kwargs["scraping_interval_hours"] = args.interval
        if args.max_articles:
            kwargs["max_articles"] = args.max_articles
        if args.active:
            kwargs["is_active"] = True
        
        success = scheduler.update_entity_config(args.name, **kwargs)
        if not success:
            sys.exit(1)
    
    elif args.command == 'scrape':
        if not args.name:
            print("Error: --name is required for scrape command")
            sys.exit(1)
        
        success = scheduler.run_scraping_for_entity(args.name)
        if not success:
            sys.exit(1)
    
    elif args.command == 'scrape-all':
        results = scheduler.run_scraping_for_all_active()
        print("Scraping Results:")
        for name, result in results.items():
            status = "✓ Success" if result["success"] else "✗ Failed"
            print(f"  {name}: {status}")
    
    elif args.command == 'check':
        entities_to_scrape = scheduler.check_scheduled_scraping()
        if entities_to_scrape:
            print("Entities that need scraping:")
            for name in entities_to_scrape:
                print(f"  - {name}")
        else:
            print("No entities need scraping at this time")
    
    elif args.command == 'stats':
        if not args.name:
            print("Error: --name is required for stats command")
            sys.exit(1)
        
        stats = scheduler.get_entity_stats(args.name)
        if "error" in stats:
            print(f"Error: {stats['error']}")
            sys.exit(1)
        
        print(f"Statistics for '{stats['name']}':")
        print(f"  Total Articles: {stats['total_articles']}")
        print(f"  Recent Articles (7 days): {stats['recent_articles']}")
        print("  Sentiment Distribution:")
        for sentiment, count in stats['sentiment_distribution'].items():
            print(f"    {sentiment}: {count}")

if __name__ == "__main__":
    main() 